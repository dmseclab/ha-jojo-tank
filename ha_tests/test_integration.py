"""Exercise actual Home Assistant platforms, MQTT dispatch and storage."""

import json
from datetime import timedelta

from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry, async_fire_mqtt_message, async_fire_time_changed,
)

from custom_components.jojo_tank.const import DOMAIN


def config():
    return {
        'tank_name':'JoJo Water Tank', 'mqtt_topic':'test/jojo/state',
        'tank_capacity':5250.0, 'tank_height':1850.0, 'sense_resistor':120.0,
        'empty_current':4.0, 'full_current':11.5, 'refill_threshold':75.0,
        'refill_timeout':15.0, 'telemetry_timeout':15.0,
        'minimum_level':20.0, 'estimation_reserve_level':10.0,
    }


async def setup(hass, options=None):
    entry = MockConfigEntry(domain=DOMAIN, data=config(), title='JoJo Water Tank', unique_id='test/jojo/state', options=options or {})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def entity_id(hass, entry, platform, key):
    return er.async_get(hass).async_get_entity_id(platform, DOMAIN, f'{entry.entry_id}_{key}')


async def send(hass, *, retained=False, voltage=1200):
    async_fire_mqtt_message(hass, 'test/jojo/state', json.dumps({'voltage_mv':voltage}), retain=retained)
    await hass.async_block_till_done()


async def test_live_expiry_and_recovery(hass, mqtt_mock, freezer):
    entry = await setup(hass)
    await send(hass)
    volume_id = entity_id(hass, entry, 'sensor', 'volume')
    online_id = entity_id(hass, entry, 'binary_sensor', 'arduino_online')
    last_id = entity_id(hass, entry, 'sensor', 'last_reading')
    assert float(hass.states.get(volume_id).state) == 4200
    assert hass.states.get(online_id).state == 'on'
    before = hass.states.get(last_id).state
    freezer.tick(timedelta(minutes=16))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert hass.states.get(online_id).state == 'off'
    assert float(hass.states.get(volume_id).state) == 4200
    assert hass.states.get(volume_id).attributes['stale'] is True
    assert hass.states.get(last_id).state == before
    await send(hass, voltage=1260)
    assert hass.states.get(online_id).state == 'on'
    assert float(hass.states.get(volume_id).state) == 4550


async def test_retained_seed_has_unknown_age(hass, mqtt_mock):
    entry = await setup(hass)
    await send(hass, retained=True)
    assert float(hass.states.get(entity_id(hass,entry,'sensor','volume')).state) == 4200
    assert hass.states.get(entity_id(hass,entry,'binary_sensor','arduino_online')).state == 'off'
    assert hass.states.get(entity_id(hass,entry,'sensor','last_reading')).state == 'unknown'


async def test_reload_restores_last_known_snapshot_and_ids(hass, mqtt_mock):
    entry = await setup(hass)
    await send(hass)
    volume_id = entity_id(hass,entry,'sensor','volume')
    last_id = entity_id(hass,entry,'sensor','last_reading')
    before = hass.states.get(last_id).state
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entity_id(hass,entry,'sensor','volume') == volume_id
    assert float(hass.states.get(volume_id).state) == 4200
    assert hass.states.get(last_id).state == before
    assert hass.states.get(entity_id(hass,entry,'binary_sensor','arduino_online')).state == 'off'


async def test_unload_removes_subscription_and_runtime(hass, mqtt_mock):
    entry = await setup(hass)
    await send(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    await send(hass)
    assert entry.entry_id not in hass.data[DOMAIN]


async def test_options_flow_applies_exact_threshold_and_timeout(hass, mqtt_mock):
    entry = await setup(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result['flow_id'], {'next_step_id':'settings'})
    assert result['step_id'] == 'settings'
    settings = {key:value for key,value in config().items() if key not in ('tank_name','mqtt_topic')}
    settings.update(refill_threshold=110.0, telemetry_timeout=25.0)
    result = await hass.config_entries.options.async_configure(result['flow_id'], settings)
    await hass.async_block_till_done()
    assert result['type'] == 'create_entry'
    assert entry.options['refill_threshold'] == 110.0
    assert float(hass.states.get(entity_id(hass,entry,'sensor','refill_threshold')).state) == 110.0


async def test_sustained_100_l_refill_records_once_and_survives_reload(hass, mqtt_mock, freezer):
    entry = await setup(hass)
    for voltage in [1200] * 8 + [1217.142857142857] * 8:
        freezer.tick(timedelta(minutes=5))
        async_fire_time_changed(hass, dt_util.utcnow())
        await hass.async_block_till_done()
        await send(hass, voltage=voltage)
    freezer.tick(timedelta(minutes=20))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    history_id = entity_id(hass,entry,'sensor','refill_history')
    state = hass.states.get(history_id)
    assert state.state == '1'
    assert state.attributes['events'][0]['amount_l'] == 100
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(history_id).attributes['events'][0]['amount_l'] == 100


async def test_weather_compensation_and_fallback(hass, mqtt_mock, freezer):
    hass.states.async_set('weather.forecast_home', 'sunny', {'temperature':35, 'temperature_unit':'°C'})
    entry = await setup(hass, {'temperature_compensation':True})
    await send(hass, voltage=(4+1755/1850*7.5)*120)
    depth_id = entity_id(hass,entry,'sensor','depth')
    raw_id = entity_id(hass,entry,'sensor','raw_depth')
    correction_id = entity_id(hass,entry,'sensor','temperature_correction')
    assert float(hass.states.get(depth_id).state) == 1830
    assert float(hass.states.get(raw_id).state) == 1755
    assert float(hass.states.get(correction_id).state) == 75
    # A broker payload cannot substitute a trusted weather correction.
    async_fire_mqtt_message(hass, 'test/jojo/state', json.dumps({'voltage_mv':1200, '_temperature_correction_mm':999}))
    await hass.async_block_till_done()
    assert float(hass.states.get(correction_id).state) == 75
    hass.states.async_set('weather.forecast_home', 'unavailable')
    await send(hass, voltage=(4+1755/1850*7.5)*120)
    assert float(hass.states.get(depth_id).state) == 1755
    assert float(hass.states.get(correction_id).state) == 0
