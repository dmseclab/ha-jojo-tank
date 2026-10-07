"""JoJo Tank Monitor integration."""

from __future__ import annotations

import json
import logging
from collections import deque
from datetime import datetime, timedelta, timezone

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store

from .calculations import finite_float, payload_float, setting as _setting, volume as _volume_from_payload
from .const import (
    CONF_MQTT_TOPIC, CONF_REFILL_THRESHOLD, CONF_REFILL_TIMEOUT, CONF_TANK_CAPACITY,
    DATA_LAST_REFILL_AMOUNT, DATA_LAST_REFILL_TIME, DATA_LATEST,
    DATA_PREVIOUS_VOLUME, DATA_REFILLING, DATA_REFILL_TIMER, DATA_UNSUB,
    DATA_REFILL_HISTORY, DATA_REFILL_START_VOLUME, DATA_REFILL_END_VOLUME,
    DEFAULT_REFILL_THRESHOLD, DEFAULT_REFILL_TIMEOUT, DOMAIN, PLATFORMS, SIGNAL_UPDATE,
)

_LOGGER = logging.getLogger(__name__)
STORAGE_VERSION = 1
MAX_REFILL_HISTORY = 100
REFILL_HISTORY_DAYS = 60
REFILL_FILTER_SAMPLES = 5
REFILL_CONFIRM_SAMPLES = 3
REFILL_BASELINE_WINDOW = 12
REFILL_NOISE_FLOOR_PERCENT = 4.0


def _uptime_from_payload(payload: dict) -> float | None:
    """Return device uptime when supplied by Rev 6 firmware."""
    uptime = payload_float(payload, "uptime_seconds")
    return uptime if uptime is not None and uptime >= 0 else None


def _load_refill_history(saved: dict) -> list[dict]:
    history = saved.get(DATA_REFILL_HISTORY, [])
    if not isinstance(history, list):
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=REFILL_HISTORY_DAYS)
    valid = []
    for event in history:
        if not isinstance(event, dict):
            continue
        try:
            event_time = datetime.fromisoformat(event["time"])
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)
        except (KeyError, TypeError, ValueError):
            continue
        if event_time >= cutoff:
            valid.append(event)
    return valid[-MAX_REFILL_HISTORY:]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if not await mqtt.async_wait_for_mqtt_client(hass):
        return False

    hass.data.setdefault(DOMAIN, {})
    store = Store[dict](hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
    saved = await store.async_load() or {}
    if not isinstance(saved, dict):
        saved = {}
    saved_time = saved.get(DATA_LAST_REFILL_TIME)
    try:
        last_refill_time = datetime.fromisoformat(saved_time) if saved_time else None
        if last_refill_time is not None and last_refill_time.tzinfo is None:
            last_refill_time = last_refill_time.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        last_refill_time = None

    runtime = {
        DATA_LATEST: {},
        DATA_REFILLING: False,
        DATA_LAST_REFILL_AMOUNT: max(0.0, finite_float(saved.get(DATA_LAST_REFILL_AMOUNT)) or 0.0),
        DATA_LAST_REFILL_TIME: last_refill_time,
        DATA_REFILL_HISTORY: _load_refill_history(saved),
        DATA_REFILL_START_VOLUME: None,
        DATA_REFILL_END_VOLUME: None,
        DATA_PREVIOUS_VOLUME: None,
        DATA_REFILL_TIMER: None,
        "previous_uptime": None,
        "last_reading": None,
        "last_live_message": None,
        "volume_samples": deque(maxlen=REFILL_FILTER_SAMPLES),
        "baseline_samples": deque(maxlen=REFILL_BASELINE_WINDOW),
        "refill_candidate_count": 0,
        "refill_candidate_start": None,
        "store": store,
    }
    hass.data[DOMAIN][entry.entry_id] = runtime
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    def refill_data() -> dict:
        return {
            DATA_LAST_REFILL_AMOUNT: runtime[DATA_LAST_REFILL_AMOUNT],
            DATA_LAST_REFILL_TIME: runtime[DATA_LAST_REFILL_TIME].isoformat()
            if runtime[DATA_LAST_REFILL_TIME] else None,
            DATA_REFILL_HISTORY: runtime[DATA_REFILL_HISTORY],
        }

    @callback
    def save_refill_history() -> None:
        # Coalesce state changes and snapshot the latest values at write time.
        store.async_delay_save(refill_data, 1.0)

    runtime["save_refill_history"] = save_refill_history

    @callback
    def finish_refill(_now=None) -> None:
        if runtime[DATA_REFILLING]:
            start_volume = runtime.get(DATA_REFILL_START_VOLUME)
            end_volume = runtime.get(DATA_REFILL_END_VOLUME)
            refill_time = runtime.get(DATA_LAST_REFILL_TIME)
            if start_volume is not None and end_volume is not None and refill_time is not None:
                event = {
                    "time": refill_time.isoformat(),
                    "start_l": round(float(start_volume)),
                    "end_l": round(float(end_volume)),
                    "amount_l": round(max(0.0, float(end_volume) - float(start_volume))),
                }
                history = _load_refill_history({DATA_REFILL_HISTORY: runtime[DATA_REFILL_HISTORY]})
                history.append(event)
                runtime[DATA_REFILL_HISTORY] = history[-MAX_REFILL_HISTORY:]
                runtime[DATA_LAST_REFILL_AMOUNT] = float(event["amount_l"])
        runtime[DATA_REFILLING] = False
        runtime[DATA_REFILL_TIMER] = None
        runtime[DATA_REFILL_START_VOLUME] = None
        runtime[DATA_REFILL_END_VOLUME] = None
        runtime["refill_candidate_count"] = 0
        runtime["refill_candidate_start"] = None
        # Re-baseline at the settled post-refill level. Without this, the
        # pre-refill low-water envelope can immediately create a duplicate
        # event after the close-out timer expires.
        if runtime["volume_samples"]:
            settled = sorted(runtime["volume_samples"])[len(runtime["volume_samples"]) // 2]
            runtime["baseline_samples"].clear()
            runtime["baseline_samples"].append(settled)
        save_refill_history()
        async_dispatcher_send(hass, f"{SIGNAL_UPDATE}_{entry.entry_id}")

    @callback
    def reset_refill_tracking(volume: float, uptime: float | None) -> None:
        """Re-baseline refill detection after a device restart."""
        if cancel := runtime.get(DATA_REFILL_TIMER):
            cancel()
        runtime[DATA_REFILLING] = False
        runtime[DATA_REFILL_TIMER] = None
        runtime[DATA_REFILL_START_VOLUME] = None
        runtime[DATA_REFILL_END_VOLUME] = None
        runtime[DATA_PREVIOUS_VOLUME] = volume
        runtime["previous_uptime"] = uptime
        runtime["volume_samples"].clear()
        runtime["baseline_samples"].clear()
        runtime["volume_samples"].append(volume)
        runtime["baseline_samples"].append(volume)
        runtime["refill_candidate_count"] = 0
        runtime["refill_candidate_start"] = None

    @callback
    def clear_refill_history() -> None:
        volume = _volume_from_payload(runtime[DATA_LATEST], entry)
        reset_refill_tracking(volume or 0.0, runtime.get("previous_uptime"))
        if volume is None:
            runtime["volume_samples"].clear()
            runtime["baseline_samples"].clear()
            runtime[DATA_PREVIOUS_VOLUME] = None
        runtime[DATA_LAST_REFILL_AMOUNT] = 0.0
        runtime[DATA_LAST_REFILL_TIME] = None
        runtime[DATA_REFILL_HISTORY] = []
        save_refill_history()

    runtime["clear_refill_history"] = clear_refill_history

    @callback
    def process_refill(payload: dict) -> None:
        """Detect sustained refills while rejecting short sensor recovery/noise."""
        volume = _volume_from_payload(payload, entry)
        if volume is None:
            return

        uptime = _uptime_from_payload(payload)
        previous_uptime = runtime.get("previous_uptime")
        if uptime is not None and uptime == previous_uptime:
            return

        if uptime is not None and previous_uptime is not None and uptime < previous_uptime:
            _LOGGER.info(
                "JoJo Tank device restart detected (uptime %.0fs -> %.0fs); refill detection re-baselined",
                previous_uptime, uptime,
            )
            reset_refill_tracking(volume, uptime)
            return

        if uptime is not None:
            runtime["previous_uptime"] = uptime

        # Five readings (normally ~25 minutes with Rev 6 firmware) are reduced
        # to their median.  A single thermal/noise excursion therefore cannot
        # become a refill event.
        samples = runtime["volume_samples"]
        samples.append(volume)
        if len(samples) < REFILL_FILTER_SAMPLES:
            runtime[DATA_PREVIOUS_VOLUME] = volume
            return

        ordered = sorted(samples)
        filtered_volume = ordered[len(ordered) // 2]
        runtime[DATA_PREVIOUS_VOLUME] = filtered_volume

        baseline_samples = runtime["baseline_samples"]
        if not baseline_samples:
            baseline_samples.append(filtered_volume)
            return

        # After a refill has been confirmed, follow its filtered high-water
        # mark without demanding another full threshold jump.  This preserves
        # the final refill amount while the close-out timer handles completion.
        if runtime[DATA_REFILLING]:
            old_end = float(runtime[DATA_REFILL_END_VOLUME] or filtered_volume)
            if filtered_volume > old_end:
                runtime[DATA_REFILL_END_VOLUME] = filtered_volume
                capacity = float(_setting(entry, CONF_TANK_CAPACITY))
                runtime[DATA_LAST_REFILL_AMOUNT] = min(
                    max(
                        0.0,
                        filtered_volume - float(runtime[DATA_REFILL_START_VOLUME]),
                    ),
                    capacity,
                )
                save_refill_history()
            # Keep an already confirmed refill open while new readings exceed
            # its filtered end. The amount still uses the median, so a spike
            # can delay close-out but cannot inflate the recorded amount.
            pending_rise = volume > old_end
            if filtered_volume > old_end or pending_rise:
                if cancel := runtime.get(DATA_REFILL_TIMER):
                    cancel()
                timeout = float(_setting(entry, CONF_REFILL_TIMEOUT, DEFAULT_REFILL_TIMEOUT))
                runtime[DATA_REFILL_TIMER] = async_call_later(
                    hass, timedelta(minutes=timeout), finish_refill
                )
            return

        # The baseline is the recent low-water envelope, not the immediately
        # preceding sample.  This makes refill detection depend on a sustained
        # net rise rather than one upward step.
        baseline = min(baseline_samples)
        configured_threshold = float(
            _setting(entry, CONF_REFILL_THRESHOLD, DEFAULT_REFILL_THRESHOLD)
        )
        capacity = float(_setting(entry, CONF_TANK_CAPACITY))
        # Preserve the beta's conservative noise floor: four percent is 210 L
        # on the reference tank. Smaller top-ups cannot be distinguished reliably
        # from measurement recovery with the available telemetry.
        threshold = max(
            configured_threshold,
            capacity * REFILL_NOISE_FLOOR_PERCENT / 100.0,
        )
        rise = filtered_volume - baseline

        if rise >= threshold:
            if runtime["refill_candidate_start"] is None:
                runtime["refill_candidate_start"] = baseline
                runtime["refill_candidate_count"] = 1
            else:
                runtime["refill_candidate_count"] += 1
        else:
            runtime["refill_candidate_count"] = 0
            runtime["refill_candidate_start"] = None
            baseline_samples.append(filtered_volume)
            return

        # Require three consecutive filtered confirmations.  With the normal
        # five-minute publish interval this is roughly 15 minutes of evidence.
        if runtime["refill_candidate_count"] < REFILL_CONFIRM_SAMPLES:
            return

        start_volume = float(runtime["refill_candidate_start"])
        runtime[DATA_REFILLING] = True
        runtime[DATA_REFILL_START_VOLUME] = start_volume
        runtime[DATA_REFILL_END_VOLUME] = filtered_volume
        runtime[DATA_LAST_REFILL_AMOUNT] = min(
            max(0.0, filtered_volume - start_volume), capacity
        )
        runtime[DATA_LAST_REFILL_TIME] = datetime.now(timezone.utc)

        # Once confirmed, keep the recent envelope close to the new level so
        # normal oscillation around that level cannot repeatedly retrigger.
        baseline_samples.clear()
        baseline_samples.append(filtered_volume)
        runtime["refill_candidate_count"] = 0
        runtime["refill_candidate_start"] = None

        save_refill_history()
        if cancel := runtime.get(DATA_REFILL_TIMER):
            cancel()
        timeout = float(_setting(entry, CONF_REFILL_TIMEOUT, DEFAULT_REFILL_TIMEOUT))
        runtime[DATA_REFILL_TIMER] = async_call_later(
            hass, timedelta(minutes=timeout), finish_refill
        )

    @callback
    def message_received(msg: mqtt.ReceiveMessage) -> None:
        try:
            payload = json.loads(msg.payload)
        except (json.JSONDecodeError, TypeError):
            _LOGGER.warning("Invalid JSON received on %s", msg.topic)
            return
        if not isinstance(payload, dict):
            _LOGGER.warning("Expected JSON object on %s", msg.topic)
            return
        if _volume_from_payload(payload, entry) is None:
            _LOGGER.warning("Invalid tank measurement received on %s", msg.topic)
            return
        now = datetime.now(timezone.utc)
        runtime["last_reading"] = now
        runtime[DATA_LATEST] = payload
        # Retained startup data may populate the display, but is not evidence
        # of a new refill. Long telemetry gaps also need a fresh baseline.
        previous_message = runtime["last_live_message"]
        gap_limit = max(15.0, float(_setting(entry, CONF_REFILL_TIMEOUT, DEFAULT_REFILL_TIMEOUT)))
        if getattr(msg, "retain", False) or (
            previous_message is not None
            and now - previous_message > timedelta(minutes=gap_limit)
        ):
            reset_refill_tracking(_volume_from_payload(payload, entry), _uptime_from_payload(payload))
        else:
            process_refill(payload)
        if not getattr(msg, "retain", False):
            runtime["last_live_message"] = now
        async_dispatcher_send(hass, f"{SIGNAL_UPDATE}_{entry.entry_id}")

    runtime[DATA_UNSUB] = await mqtt.async_subscribe(hass, entry.data[CONF_MQTT_TOPIC], message_received, qos=0)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        runtime = hass.data[DOMAIN].pop(entry.entry_id)
        if unsub := runtime.get(DATA_UNSUB):
            unsub()
        if cancel := runtime.get(DATA_REFILL_TIMER):
            cancel()
        # Flush any delayed save before discarding the runtime.
        refill_time = runtime[DATA_LAST_REFILL_TIME]
        await runtime["store"].async_save({
            DATA_LAST_REFILL_AMOUNT: runtime[DATA_LAST_REFILL_AMOUNT],
            DATA_LAST_REFILL_TIME: refill_time.isoformat() if refill_time else None,
            DATA_REFILL_HISTORY: runtime[DATA_REFILL_HISTORY],
        })
    return unloaded
