"""Config flow for JoJo Tank Monitor."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_EMPTY_CURRENT, CONF_FULL_CURRENT, CONF_MINIMUM_LEVEL, CONF_MQTT_TOPIC,
    CONF_REFILL_THRESHOLD, CONF_REFILL_TIMEOUT, CONF_SENSE_RESISTOR,
    CONF_TANK_CAPACITY, CONF_TANK_HEIGHT, CONF_TANK_NAME,
    DATA_LAST_REFILL_AMOUNT, DATA_LAST_REFILL_TIME, DATA_REFILLING,
    DEFAULT_EMPTY_CURRENT, DEFAULT_FULL_CURRENT, DEFAULT_MINIMUM_LEVEL,
    DEFAULT_MQTT_TOPIC, DEFAULT_REFILL_THRESHOLD, DEFAULT_REFILL_TIMEOUT,
    DEFAULT_SENSE_RESISTOR, DEFAULT_TANK_CAPACITY, DEFAULT_TANK_HEIGHT,
    DEFAULT_TANK_NAME, DOMAIN, SIGNAL_UPDATE,
)

CONF_RESET_REFILL_HISTORY = "reset_refill_history"


def _validate(values: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if values[CONF_FULL_CURRENT] <= values[CONF_EMPTY_CURRENT]:
        errors[CONF_FULL_CURRENT] = "full_not_greater_than_empty"
    elif values[CONF_TANK_CAPACITY] <= 0:
        errors[CONF_TANK_CAPACITY] = "must_be_positive"
    elif values[CONF_TANK_HEIGHT] <= 0:
        errors[CONF_TANK_HEIGHT] = "must_be_positive"
    elif values[CONF_SENSE_RESISTOR] <= 0:
        errors[CONF_SENSE_RESISTOR] = "must_be_positive"
    elif values[CONF_REFILL_THRESHOLD] <= 0:
        errors[CONF_REFILL_THRESHOLD] = "must_be_positive"
    elif values[CONF_REFILL_TIMEOUT] <= 0:
        errors[CONF_REFILL_TIMEOUT] = "must_be_positive"
    elif not 0 <= values.get(CONF_MINIMUM_LEVEL, DEFAULT_MINIMUM_LEVEL) <= 100:
        errors[CONF_MINIMUM_LEVEL] = "minimum_level_range"
    return errors


def _schema(defaults: dict[str, Any], include_identity: bool = True) -> vol.Schema:
    fields: dict[Any, Any] = {}
    if include_identity:
        fields[vol.Required(CONF_TANK_NAME, default=defaults.get(CONF_TANK_NAME, DEFAULT_TANK_NAME))] = str
        fields[vol.Required(CONF_MQTT_TOPIC, default=defaults.get(CONF_MQTT_TOPIC, DEFAULT_MQTT_TOPIC))] = str
    fields.update({
        vol.Required(CONF_TANK_CAPACITY, default=defaults.get(CONF_TANK_CAPACITY, DEFAULT_TANK_CAPACITY)): vol.Coerce(float),
        vol.Required(CONF_TANK_HEIGHT, default=defaults.get(CONF_TANK_HEIGHT, DEFAULT_TANK_HEIGHT)): vol.Coerce(float),
        vol.Required(CONF_EMPTY_CURRENT, default=defaults.get(CONF_EMPTY_CURRENT, DEFAULT_EMPTY_CURRENT)): vol.Coerce(float),
        vol.Required(CONF_FULL_CURRENT, default=defaults.get(CONF_FULL_CURRENT, DEFAULT_FULL_CURRENT)): vol.Coerce(float),
        vol.Required(CONF_SENSE_RESISTOR, default=defaults.get(CONF_SENSE_RESISTOR, DEFAULT_SENSE_RESISTOR)): vol.Coerce(float),
        vol.Required(CONF_REFILL_THRESHOLD, default=defaults.get(CONF_REFILL_THRESHOLD, DEFAULT_REFILL_THRESHOLD)): vol.Coerce(float),
        vol.Required(CONF_REFILL_TIMEOUT, default=defaults.get(CONF_REFILL_TIMEOUT, DEFAULT_REFILL_TIMEOUT)): vol.Coerce(float),
        vol.Required(CONF_MINIMUM_LEVEL, default=defaults.get(CONF_MINIMUM_LEVEL, DEFAULT_MINIMUM_LEVEL)): vol.Coerce(float),
    })
    return vol.Schema(fields)


class JoJoTankConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> JoJoTankOptionsFlow:
        return JoJoTankOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                await self.async_set_unique_id(user_input[CONF_MQTT_TOPIC])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=user_input[CONF_TANK_NAME], data=user_input)
        return self.async_show_form(step_id="user", data_schema=_schema(user_input or {}), errors=errors)


class JoJoTankOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
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
            menu_options=["reset_refill_history"],
        )

    async def async_step_reset_refill_history(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            if user_input.get(CONF_RESET_REFILL_HISTORY):
                runtime = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)
                if runtime is not None:
                    if cancel := runtime.get("refill_timer"):
                        cancel()
                    runtime[DATA_REFILLING] = False
                    runtime[DATA_LAST_REFILL_AMOUNT] = 0.0
                    runtime[DATA_LAST_REFILL_TIME] = None
                    runtime["refill_timer"] = None
                    store = runtime.get("store")
                    if store is not None:
                        await store.async_save({
                            DATA_LAST_REFILL_AMOUNT: 0.0,
                            DATA_LAST_REFILL_TIME: None,
                        })
                    from homeassistant.helpers.dispatcher import async_dispatcher_send
                    async_dispatcher_send(self.hass, f"{SIGNAL_UPDATE}_{self.config_entry.entry_id}")
            return self.async_create_entry(title="", data=dict(self.config_entry.options))

        return self.async_show_form(
            step_id="reset_refill_history",
            data_schema=vol.Schema({
                vol.Required(CONF_RESET_REFILL_HISTORY, default=False): bool,
            }),
        )
