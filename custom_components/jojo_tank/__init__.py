"""JoJo Tank Monitor integration."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later

from .const import (
    CONF_EMPTY_CURRENT, CONF_FULL_CURRENT, CONF_MQTT_TOPIC, CONF_REFILL_THRESHOLD,
    CONF_REFILL_TIMEOUT, CONF_SENSE_RESISTOR, CONF_TANK_CAPACITY,
    DATA_LAST_REFILL_AMOUNT, DATA_LAST_REFILL_TIME, DATA_LATEST,
    DATA_PREVIOUS_VOLUME, DATA_REFILLING, DATA_REFILL_TIMER, DATA_UNSUB,
    DEFAULT_REFILL_THRESHOLD, DEFAULT_REFILL_TIMEOUT, DOMAIN, PLATFORMS, SIGNAL_UPDATE,
)

_LOGGER = logging.getLogger(__name__)


def _setting(entry: ConfigEntry, key: str, default=None):
    return entry.options.get(key, entry.data.get(key, default))


def _volume_from_payload(payload: dict, entry: ConfigEntry) -> float | None:
    try:
        voltage = float(payload["voltage_mv"])
        resistor = float(_setting(entry, CONF_SENSE_RESISTOR))
        current = voltage / resistor
        empty = float(_setting(entry, CONF_EMPTY_CURRENT))
        full = float(_setting(entry, CONF_FULL_CURRENT))
        capacity = float(_setting(entry, CONF_TANK_CAPACITY))
        level = max(0.0, min(100.0, ((current - empty) / (full - empty)) * 100.0))
        return level / 100.0 * capacity
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if not await mqtt.async_wait_for_mqtt_client(hass):
        return False

    hass.data.setdefault(DOMAIN, {})
    runtime = {
        DATA_LATEST: {},
        DATA_REFILLING: False,
        DATA_LAST_REFILL_AMOUNT: 0.0,
        DATA_LAST_REFILL_TIME: None,
        DATA_PREVIOUS_VOLUME: None,
        DATA_REFILL_TIMER: None,
    }
    hass.data[DOMAIN][entry.entry_id] = runtime
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    @callback
    def finish_refill(_now=None) -> None:
        runtime[DATA_REFILLING] = False
        runtime[DATA_REFILL_TIMER] = None
        async_dispatcher_send(hass, f"{SIGNAL_UPDATE}_{entry.entry_id}")

    @callback
    def process_refill(payload: dict) -> None:
        volume = _volume_from_payload(payload, entry)
        if volume is None:
            return
        previous = runtime[DATA_PREVIOUS_VOLUME]
        runtime[DATA_PREVIOUS_VOLUME] = volume
        if previous is None:
            return
        increment = volume - previous
        threshold = float(_setting(entry, CONF_REFILL_THRESHOLD, DEFAULT_REFILL_THRESHOLD))
        if increment < threshold:
            return

        increment = round(increment)
        capacity = float(_setting(entry, CONF_TANK_CAPACITY))
        if not runtime[DATA_REFILLING]:
            runtime[DATA_REFILLING] = True
            runtime[DATA_LAST_REFILL_AMOUNT] = min(float(increment), capacity)
            runtime[DATA_LAST_REFILL_TIME] = datetime.now(timezone.utc)
        else:
            runtime[DATA_LAST_REFILL_AMOUNT] = min(
                float(runtime[DATA_LAST_REFILL_AMOUNT]) + float(increment), capacity
            )

        if cancel := runtime.get(DATA_REFILL_TIMER):
            cancel()
        timeout = float(_setting(entry, CONF_REFILL_TIMEOUT, DEFAULT_REFILL_TIMEOUT))
        runtime[DATA_REFILL_TIMER] = async_call_later(hass, timedelta(minutes=timeout), finish_refill)

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
        runtime[DATA_LATEST] = payload
        process_refill(payload)
        async_dispatcher_send(hass, f"{SIGNAL_UPDATE}_{entry.entry_id}")

    runtime[DATA_UNSUB] = await mqtt.async_subscribe(
        hass, entry.data[CONF_MQTT_TOPIC], message_received, qos=0
    )
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
    return unloaded
