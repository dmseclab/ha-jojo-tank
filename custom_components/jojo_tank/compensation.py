"""Bounded, opt-in weather compensation sampled only with live telemetry."""

from datetime import timedelta

from .calculations import finite_float, raw_depth, setting
from .const import (
    CONF_TEMPERATURE_COMPENSATION, CONF_WEATHER_ENTITY,
    CONF_TEMPERATURE_REFERENCE, CONF_TEMPERATURE_COEFFICIENT, CONF_TEMPERATURE_CAP,
    DEFAULT_TEMPERATURE_COMPENSATION, DEFAULT_WEATHER_ENTITY,
    DEFAULT_TEMPERATURE_REFERENCE, DEFAULT_TEMPERATURE_COEFFICIENT, DEFAULT_TEMPERATURE_CAP,
)


def apply_compensation(payload, entry, hass, now):
    """Annotate a trusted snapshot; MQTT cannot supply its own correction."""
    payload["_temperature_correction_mm"] = 0.0
    payload["_compensation_status"] = "Disabled"
    if not setting(entry, CONF_TEMPERATURE_COMPENSATION, DEFAULT_TEMPERATURE_COMPENSATION):
        return
    payload["_compensation_status"] = "Weather unavailable"
    state = hass.states.get(setting(entry, CONF_WEATHER_ENTITY, DEFAULT_WEATHER_ENTITY))
    if state is None or state.state in {"unknown", "unavailable"}:
        return
    # last_updated also changes with attributes. last_changed only tracks condition.
    age = now - state.last_updated
    if age < timedelta(0) or age > timedelta(hours=2):
        payload["_compensation_status"] = "Weather stale"
        return
    temperature = finite_float(state.attributes.get("temperature"))
    unit = state.attributes.get("temperature_unit")
    if temperature is None or unit not in {"°C", "°F"}:
        payload["_compensation_status"] = "Invalid temperature"
        return
    if unit == "°F":
        temperature = (temperature - 32.0) * 5.0 / 9.0
    payload["_ambient_temperature_c"] = temperature
    if not 0.0 <= temperature <= 45.0:
        payload["_compensation_status"] = "Temperature outside trial range"
        return
    reference = finite_float(setting(entry, CONF_TEMPERATURE_REFERENCE, DEFAULT_TEMPERATURE_REFERENCE))
    coefficient = finite_float(setting(entry, CONF_TEMPERATURE_COEFFICIENT, DEFAULT_TEMPERATURE_COEFFICIENT))
    cap = finite_float(setting(entry, CONF_TEMPERATURE_CAP, DEFAULT_TEMPERATURE_CAP))
    if reference is None or coefficient is None or cap is None or not 0 <= reference <= 45 or not 0 <= coefficient <= 10 or not 0 <= cap <= 100:
        payload["_compensation_status"] = "Invalid settings"
        return
    raw = raw_depth(payload, entry)
    if raw is None or raw <= 0:
        payload["_compensation_status"] = "Empty or invalid measurement"
        return
    payload["_temperature_correction_mm"] = min(cap, max(0.0, temperature - reference) * coefficient)
    payload["_compensation_status"] = "Active"
