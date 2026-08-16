"""JoJo Tank Monitor integration."""

from __future__ import annotations

import json
import logging

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DATA_LATEST, DATA_UNSUB, DOMAIN, PLATFORMS, SIGNAL_UPDATE, CONF_MQTT_TOPIC

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up JoJo Tank Monitor from a config entry."""
    if not await mqtt.async_wait_for_mqtt_client(hass):
        return False

    hass.data.setdefault(DOMAIN, {})
    runtime = {DATA_LATEST: {}}
    hass.data[DOMAIN][entry.entry_id] = runtime
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

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
        async_dispatcher_send(hass, f"{SIGNAL_UPDATE}_{entry.entry_id}")

    runtime[DATA_UNSUB] = await mqtt.async_subscribe(hass, entry.data[CONF_MQTT_TOPIC], message_received, qos=0)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload after an options change so calculations update immediately."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        runtime = hass.data[DOMAIN].pop(entry.entry_id)
        if unsub := runtime.get(DATA_UNSUB):
            unsub()
    return unloaded
