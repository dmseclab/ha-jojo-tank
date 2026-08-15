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


class JoJoTankConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for JoJo Tank Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input[CONF_FULL_CURRENT] <= user_input[CONF_EMPTY_CURRENT]:
                errors[CONF_FULL_CURRENT] = "full_not_greater_than_empty"
            elif user_input[CONF_TANK_CAPACITY] <= 0:
                errors[CONF_TANK_CAPACITY] = "must_be_positive"
            elif user_input[CONF_TANK_HEIGHT] <= 0:
                errors[CONF_TANK_HEIGHT] = "must_be_positive"
            elif user_input[CONF_SENSE_RESISTOR] <= 0:
                errors[CONF_SENSE_RESISTOR] = "must_be_positive"
            else:
                await self.async_set_unique_id(user_input[CONF_MQTT_TOPIC])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_TANK_NAME], data=user_input
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_TANK_NAME, default=DEFAULT_TANK_NAME): str,
                vol.Required(CONF_MQTT_TOPIC, default=DEFAULT_MQTT_TOPIC): str,
                vol.Required(
                    CONF_TANK_CAPACITY, default=DEFAULT_TANK_CAPACITY
                ): vol.Coerce(float),
                vol.Required(
                    CONF_TANK_HEIGHT, default=DEFAULT_TANK_HEIGHT
                ): vol.Coerce(float),
                vol.Required(
                    CONF_EMPTY_CURRENT, default=DEFAULT_EMPTY_CURRENT
                ): vol.Coerce(float),
                vol.Required(
                    CONF_FULL_CURRENT, default=DEFAULT_FULL_CURRENT
                ): vol.Coerce(float),
                vol.Required(
                    CONF_SENSE_RESISTOR, default=DEFAULT_SENSE_RESISTOR
                ): vol.Coerce(float),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
