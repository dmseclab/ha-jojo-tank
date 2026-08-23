"""Binary sensor platform for JoJo Tank Monitor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_EMPTY_CURRENT,
    CONF_FULL_CURRENT,
    CONF_MINIMUM_LEVEL,
    CONF_SENSE_RESISTOR,
    CONF_TANK_NAME,
    DATA_LATEST,
    DEFAULT_MINIMUM_LEVEL,
    DOMAIN,
    SIGNAL_UPDATE,
)

LOW_WATER_CLEAR_MARGIN = 2.0


def _setting(entry: ConfigEntry, key: str, default: Any = None) -> Any:
    return entry.options.get(key, entry.data.get(key, default))


def _level(data: dict[str, Any], entry: ConfigEntry) -> float | None:
    try:
        voltage = float(data["voltage_mv"])
        resistor = float(_setting(entry, CONF_SENSE_RESISTOR))
        current = voltage / resistor
        empty = float(_setting(entry, CONF_EMPTY_CURRENT))
        full = float(_setting(entry, CONF_FULL_CURRENT))
        level = ((current - empty) / (full - empty)) * 100.0
        return max(0.0, min(100.0, level))
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([JoJoLowWaterBinarySensor(hass, entry)])


class JoJoLowWaterBinarySensor(BinarySensorEntity):
    """Indicate low water with hysteresis around the configured minimum."""

    _attr_has_entity_name = True
    _attr_name = "Low Water"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_low_water"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data[CONF_TANK_NAME],
            manufacturer="DIY / DFRobot",
            model="Arduino UNO R4 WiFi + submersible pressure sensor",
        )
        self._update_value()

    @callback
    def _update_value(self) -> None:
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]
        level = _level(runtime[DATA_LATEST], self.entry)
        if level is None:
            self._attr_is_on = None
            return

        minimum = float(_setting(self.entry, CONF_MINIMUM_LEVEL, DEFAULT_MINIMUM_LEVEL))

        # Hysteresis prevents the binary sensor from repeatedly toggling when
        # the measured level hovers around the configured minimum. Enter the
        # low-water state at/below the threshold, but only clear it after the
        # level has recovered LOW_WATER_CLEAR_MARGIN percentage points above it.
        if self._attr_is_on:
            self._attr_is_on = level < (minimum + LOW_WATER_CLEAR_MARGIN)
        else:
            self._attr_is_on = level <= minimum

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_UPDATE}_{self.entry.entry_id}",
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        self._update_value()
        self.async_write_ha_state()
