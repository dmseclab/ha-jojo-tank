"""Config flow for JoJo Tank Monitor."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_EMPTY_CURRENT,
    CONF_FULL_CURRENT,
    CONF_MQTT_TOPIC,
    CONF_SENSE_RESISTOR,
    CONF_TANK_CAPACITY,
    CONF_TANK_HEIGHT,
    CONF_TANK_NAME,
    DEFAULT_EMPTY_CURRENT,
    DEFAULT_FULL_CURRENT,
    DEFAULT_MQTT_TOPIC,
    DEFAULT_SENSE_RESISTOR,
    DEFAULT_TANK_CAPACITY,
    DEFAULT_TANK_HEIGHT,
    DEFAULT_TANK_NAME,
    DOMAIN,
)


def _validate(values: dict[str, Any]) -> dict[str, str]:
    """Validate tank configuration values."""
    errors: dict[str, str] = {}
    if values[CONF_FULL_CURRENT] <= values[CONF_EMPTY_CURRENT]:
        errors[CONF_FULL_CURRENT] = "full_not_greater_than_empty"
    elif values[CONF_TANK_CAPACITY] <= 0:
        errors[CONF_TANK_CAPACITY] = "must_be_positive"
    elif values[CONF_TANK_HEIGHT] <= 0:
        errors[CONF_TANK_HEIGHT] = "must_be_positive"
    elif values[CONF_SENSE_RESISTOR] <= 0:
        errors[CONF_SENSE_RESISTOR] = "must_be_positive"
    return errors


def _schema(defaults: dict[str, Any], include_identity: bool = True) -> vol.Schema:
    """Build the config/options schema."""
    fields: dict[Any, Any] = {}
    if include_identity:
        fields[vol.Required(CONF_TANK_NAME, default=defaults.get(CONF_TANK_NAME, DEFAULT_TANK_NAME))] = str
        fields[vol.Required(CONF_MQTT_TOPIC, default=defaults.get(CONF_MQTT_TOPIC, DEFAULT_MQTT_TOPIC))] = str
    fields.update(
        {
            vol.Required(CONF_TANK_CAPACITY, default=defaults.get(CONF_TANK_CAPACITY, DEFAULT_TANK_CAPACITY)): vol.Coerce(float),
            vol.Required(CONF_TANK_HEIGHT, default=defaults.get(CONF_TANK_HEIGHT, DEFAULT_TANK_HEIGHT)): vol.Coerce(float),
            vol.Required(CONF_EMPTY_CURRENT, default=defaults.get(CONF_EMPTY_CURRENT, DEFAULT_EMPTY_CURRENT)): vol.Coerce(float),
            vol.Required(CONF_FULL_CURRENT, default=defaults.get(CONF_FULL_CURRENT, DEFAULT_FULL_CURRENT)): vol.Coerce(float),
            vol.Required(CONF_SENSE_RESISTOR, default=defaults.get(CONF_SENSE_RESISTOR, DEFAULT_SENSE_RESISTOR)): vol.Coerce(float),
        }
    )
    return vol.Schema(fields)


class JoJoTankConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for JoJo Tank Monitor."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> JoJoTankOptionsFlow:
        """Return the options flow handler."""
        return JoJoTankOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                await self.async_set_unique_id(user_input[CONF_MQTT_TOPIC])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=user_input[CONF_TANK_NAME], data=user_input)
        return self.async_show_form(step_id="user", data_schema=_schema(user_input or {}), errors=errors)


class JoJoTankOptionsFlow(config_entries.OptionsFlow):
    """Allow tank calibration/settings to be changed after setup."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage configurable tank values."""
        errors: dict[str, str] = {}
        defaults = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                return self.async_create_entry(title="", data=user_input)
            defaults.update(user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(defaults, include_identity=False),
            errors=errors,
        )
