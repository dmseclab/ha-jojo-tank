"""Small deterministic HA boundary doubles; integration code runs unmodified.

These tests cover our callbacks/calculations, not a full Home Assistant runtime.
"""

import importlib
import sys
import types
from dataclasses import make_dataclass, field
from datetime import datetime, timedelta, timezone


class Clock:
    now = datetime(2026, 10, 7, tzinfo=timezone.utc)
    timers = []

    @classmethod
    def reset(cls):
        cls.now = datetime(2026, 10, 7, tzinfo=timezone.utc)
        cls.timers = []

    @classmethod
    def advance_to(cls, when):
        while True:
            due = sorted((t for t in cls.timers if not t['cancelled'] and t['at'] <= when), key=lambda t: t['at'])
            if not due:
                break
            timer = due[0]
            cls.now = timer['at']
            timer['cancelled'] = True
            timer['callback'](cls.now)
        cls.now = when


class TestDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return Clock.now.astimezone(tz) if tz else Clock.now.replace(tzinfo=None)


class Store:
    def __class_getitem__(cls, _item):
        return cls

    def __init__(self, hass, _version, _key):
        self.saved = hass.saved
        self.pending = None
        hass.store = self

    async def async_load(self):
        return self.saved

    async def async_save(self, data):
        self.saved = data
        self.pending = None

    def async_delay_save(self, data_func, _delay):
        self.pending = data_func


class Entity:
    _attr_is_on = None

    def async_on_remove(self, callback):
        pass

    def async_write_ha_state(self):
        pass


class Flow:
    def __init_subclass__(cls, **kwargs):
        pass

    def async_create_entry(self, **kwargs):
        return kwargs


def module(name, **attrs):
    obj = types.ModuleType(name)
    obj.__dict__.update(attrs)
    sys.modules[name] = obj
    return obj


def install_doubles():
    module('homeassistant')
    module('homeassistant.components')
    module('homeassistant.helpers')
    module('homeassistant.config_entries', ConfigEntry=object, ConfigFlow=Flow, OptionsFlow=Flow)
    module('homeassistant.core', HomeAssistant=object, callback=lambda func: func)
    module('homeassistant.helpers.storage', Store=Store)
    module('homeassistant.helpers.dispatcher', async_dispatcher_send=lambda *args: None, async_dispatcher_connect=lambda *args: lambda: None)
    module('homeassistant.helpers.device_registry', DeviceInfo=lambda **kwargs: kwargs)
    module('homeassistant.helpers.entity_platform', AddEntitiesCallback=object)
    module('homeassistant.data_entry_flow', FlowResult=dict)

    async def wait(_hass):
        return True

    async def subscribe(hass, _topic, callback, qos=0):
        hass.receive = callback
        return lambda: setattr(hass, 'unsubscribed', True)

    def call_later(_hass, delay, callback):
        timer = {'at': Clock.now + delay, 'callback': callback, 'cancelled': False}
        Clock.timers.append(timer)
        return lambda: timer.update(cancelled=True)

    module('homeassistant.components.mqtt', async_wait_for_mqtt_client=wait, async_subscribe=subscribe, ReceiveMessage=object)
    module('homeassistant.helpers.event', async_call_later=call_later)
    enum = types.SimpleNamespace(MOISTURE='moisture', VOLUME_STORAGE='volume_storage', DISTANCE='distance', VOLUME='volume', TIMESTAMP='timestamp', VOLTAGE='voltage', SIGNAL_STRENGTH='signal_strength', DURATION='duration', MEASUREMENT='measurement', PROBLEM='problem', DIAGNOSTIC='diagnostic', CONNECTIVITY='connectivity')
    fields = ['key', 'name', 'native_unit_of_measurement', 'device_class', 'state_class', 'suggested_display_precision', 'entity_category', 'entity_registry_enabled_default', 'icon']
    description = make_dataclass('SensorEntityDescription', [(k, object, field(default=None)) for k in fields], frozen=True, kw_only=True)
    module('homeassistant.components.sensor', SensorDeviceClass=enum, SensorStateClass=enum, SensorEntity=Entity, SensorEntityDescription=description)
    module('homeassistant.components.binary_sensor', BinarySensorDeviceClass=enum, BinarySensorEntity=Entity)
    units = types.SimpleNamespace(MILLIVOLT='mV', MILLIMETERS='mm', SECONDS='s', LITERS='L')
    module('homeassistant.const', PERCENTAGE='%', SIGNAL_STRENGTH_DECIBELS_MILLIWATT='dBm', EntityCategory=enum, UnitOfElectricPotential=units, UnitOfLength=units, UnitOfTime=units, UnitOfVolume=units)
    module('voluptuous', Schema=lambda fields: fields, Required=lambda key, **kwargs: key, Coerce=lambda kind: kind)


install_doubles()
integration = importlib.import_module('custom_components.jojo_tank')
integration.datetime = TestDateTime
sensor = importlib.import_module('custom_components.jojo_tank.sensor')
binary_sensor = importlib.import_module('custom_components.jojo_tank.binary_sensor')
config_flow = importlib.import_module('custom_components.jojo_tank.config_flow')
calculations = importlib.import_module('custom_components.jojo_tank.calculations')
const = importlib.import_module('custom_components.jojo_tank.const')


class Harness:
    def __init__(self, saved=None, **options):
        data = {key.removeprefix('DEFAULT_').lower(): value for key, value in vars(const).items() if key.startswith('DEFAULT_')}
        self.entry = types.SimpleNamespace(entry_id='test_tank', data=data, options=options, async_on_unload=lambda _cb: None, add_update_listener=lambda _cb: lambda: None)

        async def forward(*args):
            pass

        async def unload(*args):
            return True

        self.hass = types.SimpleNamespace(data={}, saved=saved, unsubscribed=False, config_entries=types.SimpleNamespace(async_forward_entry_setups=forward, async_unload_platforms=unload))

    async def setup(self):
        await integration.async_setup_entry(self.hass, self.entry)
        self.runtime = self.hass.data[const.DOMAIN][self.entry.entry_id]
        return self

    def send(self, volume=None, *, payload=None, uptime=None, retain=False, minutes=5):
        import json
        Clock.advance_to(Clock.now + timedelta(minutes=minutes))
        if payload is None:
            current = 4.0 + float(volume) / self.entry.data['tank_capacity'] * 7.5
            payload = {'voltage_mv': current * 120}
        if uptime is not None:
            payload['uptime_seconds'] = uptime
        self.hass.receive(types.SimpleNamespace(payload=json.dumps(payload), topic='test', retain=retain))

    def settle(self, minutes=20):
        Clock.advance_to(Clock.now + timedelta(minutes=minutes))

    def pending_data(self):
        return self.hass.store.pending() if self.hass.store.pending else self.hass.store.saved
