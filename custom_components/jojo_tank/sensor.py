"""Sensor platform for JoJo Tank Monitor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, EntityCategory, UnitOfElectricPotential, UnitOfLength, UnitOfTime, UnitOfVolume
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_EMPTY_CURRENT, CONF_FULL_CURRENT, CONF_SENSE_RESISTOR, CONF_TANK_CAPACITY, CONF_TANK_HEIGHT, CONF_TANK_NAME, DATA_LAST_REFILL_AMOUNT, DATA_LAST_REFILL_TIME, DATA_LATEST, DATA_REFILLING, DOMAIN, SIGNAL_UPDATE


@dataclass(frozen=True, kw_only=True)
class JoJoSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any], ConfigEntry], Any] | None = None
    runtime_key: str | None = None


def _setting(entry: ConfigEntry, key: str) -> Any:
    return entry.options.get(key, entry.data[key])


def _float(data: dict[str, Any], key: str) -> float | None:
    try:
        return float(data[key])
    except (KeyError, TypeError, ValueError):
        return None


def _current(data: dict[str, Any], entry: ConfigEntry) -> float | None:
    voltage = _float(data, "voltage_mv")
    if voltage is not None:
        return voltage / float(_setting(entry, CONF_SENSE_RESISTOR))
    return _float(data, "current_raw_ma")


def _level(data: dict[str, Any], entry: ConfigEntry) -> float | None:
    current = _current(data, entry)
    if current is None:
        return None
    empty = float(_setting(entry, CONF_EMPTY_CURRENT))
    full = float(_setting(entry, CONF_FULL_CURRENT))
    level = ((current - empty) / (full - empty)) * 100.0
    return max(0.0, min(100.0, level))


def _volume(data: dict[str, Any], entry: ConfigEntry) -> float | None:
    level = _level(data, entry)
    return None if level is None else level / 100.0 * float(_setting(entry, CONF_TANK_CAPACITY))


def _depth(data: dict[str, Any], entry: ConfigEntry) -> float | None:
    level = _level(data, entry)
    return None if level is None else level / 100.0 * float(_setting(entry, CONF_TANK_HEIGHT))


SENSORS: tuple[JoJoSensorDescription, ...] = (
    JoJoSensorDescription(key="level", name="Tank Level", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.MOISTURE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, value_fn=_level),
    JoJoSensorDescription(key="volume", name="Available Water", native_unit_of_measurement=UnitOfVolume.LITERS, device_class=SensorDeviceClass.VOLUME_STORAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, value_fn=_volume),
    JoJoSensorDescription(key="depth", name="Water Depth", native_unit_of_measurement=UnitOfLength.MILLIMETERS, device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, value_fn=_depth),
    JoJoSensorDescription(key="current", name="Sensor Current", native_unit_of_measurement="mA", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2, value_fn=_current),
    JoJoSensorDescription(key="refill_status", name="Refill Status", runtime_key=DATA_REFILLING),
    JoJoSensorDescription(key="last_refill_amount", name="Last Refill Amount", native_unit_of_measurement=UnitOfVolume.LITERS, device_class=SensorDeviceClass.VOLUME, suggested_display_precision=0, runtime_key=DATA_LAST_REFILL_AMOUNT),
    JoJoSensorDescription(key="last_refill_time", name="Last Refill Time", device_class=SensorDeviceClass.TIMESTAMP, runtime_key=DATA_LAST_REFILL_TIME),
    JoJoSensorDescription(key="raw_adc", name="Raw ADC", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, value_fn=lambda data, entry: _float(data, "raw_adc")),
    JoJoSensorDescription(key="voltage", name="Sensor Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, value_fn=lambda data, entry: _float(data, "voltage_mv")),
    JoJoSensorDescription(key="wifi", name="Wi-Fi Signal", native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT, device_class=SensorDeviceClass.SIGNAL_STRENGTH, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, value_fn=lambda data, entry: _float(data, "wifi_rssi")),
    JoJoSensorDescription(key="uptime", name="Uptime", native_unit_of_measurement=UnitOfTime.SECONDS, device_class=SensorDeviceClass.DURATION, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, value_fn=lambda data, entry: _float(data, "uptime_seconds")),
    JoJoSensorDescription(key="firmware", name="Firmware", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, value_fn=lambda data, entry: data.get("firmware")),
    JoJoSensorDescription(key="last_reading", name="Last Reading", device_class=SensorDeviceClass.TIMESTAMP, value_fn=lambda data, entry: datetime.now(timezone.utc) if data else None),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities(JoJoTankSensor(hass, entry, description) for description in SENSORS)


class JoJoTankSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, description: JoJoSensorDescription) -> None:
        self.hass = hass
        self.entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
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
        if self.entity_description.runtime_key is not None:
            value = runtime.get(self.entity_description.runtime_key)
            if self.entity_description.key == "refill_status":
                value = "Refilling" if value else "Not Refilling"
        else:
            data = runtime[DATA_LATEST]
            value = self.entity_description.value_fn(data, self.entry) if self.entity_description.value_fn else None
        if isinstance(value, float) and self.entity_description.key in {"level", "volume", "depth", "current", "raw_adc", "voltage", "wifi", "uptime", "last_refill_amount"}:
            value = round(value, 2)
        self._attr_native_value = value

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(self.hass, f"{SIGNAL_UPDATE}_{self.entry.entry_id}", self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self._update_value()
        self.async_write_ha_state()
