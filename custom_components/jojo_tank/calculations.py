"""Shared, finite tank calculations for sensors and refill detection."""

from __future__ import annotations

from math import isfinite

from .const import (
    CONF_EMPTY_CURRENT, CONF_FULL_CURRENT, CONF_SENSE_RESISTOR,
    CONF_TANK_CAPACITY, CONF_TANK_HEIGHT,
)


def setting(entry, key: str, default=None):
    """Prefer options while preserving existing entry data."""
    return entry.options.get(key, entry.data.get(key, default))


def finite_float(value) -> float | None:
    """Reject missing, boolean, infinite and NaN telemetry/settings."""
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if isfinite(number) else None


def payload_float(data: dict, key: str) -> float | None:
    return finite_float(data.get(key))


def current(data: dict, entry) -> float | None:
    """Use voltage when present; support current-only MQTT sources."""
    if "voltage_mv" not in data:
        return payload_float(data, "current_raw_ma")
    voltage = payload_float(data, "voltage_mv")
    resistor = finite_float(setting(entry, CONF_SENSE_RESISTOR))
    if voltage is None or resistor is None or resistor <= 0:
        return None
    return finite_float(voltage / resistor)


def raw_depth(data: dict, entry) -> float | None:
    """Unclamped physical depth; keep above-full readings for diagnostics."""
    measured = current(data, entry)
    empty = finite_float(setting(entry, CONF_EMPTY_CURRENT))
    full = finite_float(setting(entry, CONF_FULL_CURRENT))
    height = finite_float(setting(entry, CONF_TANK_HEIGHT))
    if measured is None or empty is None or full is None or height is None or full <= empty or height <= 0:
        return None
    value = finite_float((measured - empty) / (full - empty) * height)
    return None if value is None else max(0.0, value)


def depth(data: dict, entry) -> float | None:
    raw = raw_depth(data, entry)
    if raw is None:
        return None
    correction = finite_float(data.get("_temperature_correction_mm", 0.0)) or 0.0
    return finite_float(raw + max(0.0, min(100.0, correction)))


def level(data: dict, entry) -> float | None:
    measured = depth(data, entry)
    height = finite_float(setting(entry, CONF_TANK_HEIGHT))
    if measured is None or height is None or height <= 0:
        return None
    return max(0.0, min(100.0, measured / height * 100.0))


def _scaled_level(data: dict, entry, key: str) -> float | None:
    percent = level(data, entry)
    scale = finite_float(setting(entry, key))
    if percent is None or scale is None or scale <= 0:
        return None
    return finite_float(percent / 100.0 * scale)


def volume(data: dict, entry) -> float | None:
    return _scaled_level(data, entry, CONF_TANK_CAPACITY)
