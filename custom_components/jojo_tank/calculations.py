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


def level(data: dict, entry) -> float | None:
    measured = current(data, entry)
    empty = finite_float(setting(entry, CONF_EMPTY_CURRENT))
    full = finite_float(setting(entry, CONF_FULL_CURRENT))
    if measured is None or empty is None or full is None or full <= empty:
        return None
    percent = finite_float((measured - empty) / (full - empty) * 100.0)
    return None if percent is None else max(0.0, min(100.0, percent))


def _scaled_level(data: dict, entry, key: str) -> float | None:
    percent = level(data, entry)
    scale = finite_float(setting(entry, key))
    if percent is None or scale is None or scale <= 0:
        return None
    return finite_float(percent / 100.0 * scale)


def volume(data: dict, entry) -> float | None:
    return _scaled_level(data, entry, CONF_TANK_CAPACITY)


def depth(data: dict, entry) -> float | None:
    return _scaled_level(data, entry, CONF_TANK_HEIGHT)
