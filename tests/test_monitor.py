"""Regression coverage for noise, refills, persistence and MQTT callbacks."""

import unittest

from tests.support import Clock, Harness, calculations, sensor, binary_sensor, config_flow, integration


class MonitorTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        Clock.reset()
        self.h = await Harness().setup()

    def warm(self, volume=4500):
        for _ in range(8):
            self.h.send(volume)

    def refill(self):
        self.warm()
        for _ in range(6):
            self.h.send(5000)

    async def test_sustained_refill_closes_once_and_preserves_amount(self):
        self.refill()
        self.assertTrue(self.h.runtime['refilling'])
        self.h.settle()
        history = self.h.runtime['refill_history']
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['amount_l'], 500)
        for _ in range(20):
            self.h.send(5000)
        self.assertEqual(len(self.h.runtime['refill_history']), 1)

    async def test_single_spike_and_sub_threshold_recovery_are_rejected(self):
        self.warm()
        self.h.send(5250)
        for volume in [4500] * 6 + [4550] * 12:
            self.h.send(volume)
        self.h.settle()
        self.assertEqual(self.h.runtime['refill_history'], [])

    async def test_slow_refill_extends_timer_on_accumulated_rises(self):
        self.refill()
        for volume in range(5005, 5105, 5):
            self.h.send(volume)
            self.assertTrue(self.h.runtime['refilling'])
        for _ in range(3):
            self.h.send(5100)
        self.h.settle()
        self.assertEqual(self.h.runtime['refill_history'][0]['amount_l'], 600)

    async def test_device_restart_rebaselines_without_a_refill(self):
        for n in range(8):
            self.h.send(4500, uptime=1000+n*300)
        self.h.send(5000, uptime=1)
        for n in range(8):
            self.h.send(5000, uptime=301+n*300)
        self.h.settle()
        self.assertEqual(self.h.runtime['refill_history'], [])

    async def test_duplicate_uptime_does_not_confirm_a_candidate(self):
        self.warm()
        for _ in range(10):
            self.h.send(5000, uptime=10000)
        self.assertFalse(self.h.runtime['refilling'])

    async def test_retained_message_and_gap_rebaseline(self):
        self.warm()
        self.h.send(5000, retain=True)
        for _ in range(8):
            self.h.send(4500)
        self.h.send(5250, minutes=60)
        for _ in range(8):
            self.h.send(5250)
        self.h.settle()
        self.assertEqual(self.h.runtime['refill_history'], [])

    async def test_invalid_payload_does_not_replace_measurement_or_timestamp(self):
        self.h.send(4500)
        latest = self.h.runtime['latest']
        last = self.h.runtime['last_reading']
        for value in [None, True, 'NaN', 'Infinity', [], {}]:
            self.h.send(payload={'voltage_mv': value})
        self.assertIs(self.h.runtime['latest'], latest)
        self.assertEqual(self.h.runtime['last_reading'], last)

    async def test_last_reading_is_stable_on_dispatcher_updates(self):
        self.h.send(4500)
        description = next(x for x in sensor.SENSORS if x.key == 'last_reading')
        entity = sensor.JoJoTankSensor(self.h.hass, self.h.entry, description)
        first = entity._attr_native_value
        self.h.settle()
        entity._handle_update()
        self.assertEqual(entity._attr_native_value, first)
        self.assertFalse(entity._attr_should_poll)

    async def test_clear_removes_events_and_candidate_baseline(self):
        self.refill()
        self.h.settle()
        flow = config_flow.JoJoTankOptionsFlow()
        flow.hass = self.h.hass
        flow.config_entry = self.h.entry
        await flow.async_step_reset_refill_history({'reset_refill_history': True})
        self.assertEqual(self.h.runtime['refill_history'], [])
        self.assertEqual(self.h.pending_data()['refill_history'], [])
        self.assertIsNone(self.h.runtime['last_refill_time'])
        for _ in range(8):
            self.h.send(5000)
        self.assertFalse(self.h.runtime['refilling'])

    async def test_clear_during_active_refill_cancels_timer(self):
        self.refill()
        self.h.runtime['clear_refill_history']()
        self.h.settle()
        self.assertEqual(self.h.runtime['refill_history'], [])
        self.assertEqual(self.h.runtime['last_refill_amount'], 0)

    async def test_unload_flushes_then_restart_loads_history(self):
        self.refill()
        self.h.settle()
        await integration.async_unload_entry(self.h.hass, self.h.entry)
        self.assertTrue(self.h.hass.unsubscribed)
        self.assertIsNone(self.h.hass.store.pending)
        next_h = await Harness(saved=self.h.hass.store.saved).setup()
        self.assertEqual(next_h.runtime['refill_history'][0]['amount_l'], 500)
        self.assertEqual(next_h.runtime['last_refill_amount'], 500)

    async def test_malformed_saved_state_and_history_are_tolerated(self):
        h = await Harness(saved={'last_refill_amount':'NaN', 'last_refill_time':'bad', 'refill_history':[None, {}, {'time':'bad'}]}).setup()
        self.assertEqual(h.runtime['last_refill_amount'], 0)
        self.assertEqual(h.runtime['refill_history'], [])

    async def test_shared_current_fallback_and_low_water_hysteresis(self):
        low = binary_sensor.JoJoLowWaterBinarySensor(self.h.hass, self.h.entry)
        for percent, expected in [(19, True), (21, True), (22, False), (20, True)]:
            self.h.send(payload={'current_raw_ma':4+percent/100*7.5})
            low._handle_update()
            self.assertEqual(low._attr_is_on, expected)
        self.assertFalse(low._attr_should_poll)
        self.assertAlmostEqual(calculations.volume({'current_raw_ma':11.5}, self.h.entry),5250)

    async def test_bad_calibration_never_divides_or_publishes_nan(self):
        for options in [{'sense_resistor':0}, {'full_current':4}, {'tank_capacity':float('inf')}]:
            h = await Harness(**options).setup()
            self.assertIsNone(calculations.volume({'voltage_mv':1380}, h.entry))
        values = dict(self.h.entry.data, sense_resistor=float('nan'))
        self.assertEqual(config_flow._validate(values), {'sense_resistor':'invalid_number'})

    async def test_configured_threshold_has_no_hidden_floor(self):
        self.warm()
        for _ in range(8):
            self.h.send(4600)
        self.h.settle()
        self.assertEqual(self.h.runtime['refill_history'][0]['amount_l'], 100)

    async def test_explicit_210_threshold_rejects_100_l_rise(self):
        self.h = await Harness(refill_threshold=210).setup()
        self.warm()
        for _ in range(8):
            self.h.send(4600)
        self.h.settle()
        self.assertEqual(self.h.runtime['refill_history'], [])

    async def test_expiry_keeps_last_known_value_and_marks_offline(self):
        self.h.send(4500)
        description = next(x for x in sensor.SENSORS if x.key == 'volume')
        entity = sensor.JoJoTankSensor(self.h.hass, self.h.entry, description)
        online = binary_sensor.JoJoArduinoOnlineBinarySensor(self.h.hass, self.h.entry)
        self.assertTrue(online._attr_is_on)
        last = self.h.runtime['last_reading']
        self.h.settle(16)
        entity._handle_update()
        online._handle_update()
        self.assertEqual(entity._attr_native_value, 4500)
        self.assertTrue(entity._attr_extra_state_attributes['stale'])
        self.assertFalse(online._attr_is_on)
        self.assertEqual(last, self.h.runtime['last_reading'])
        self.h.send(4400)
        online._handle_update()
        self.assertTrue(online._attr_is_on)

    async def test_restart_restores_snapshot_without_claiming_online(self):
        self.h.send(4500)
        last = self.h.runtime['last_reading']
        await integration.async_unload_entry(self.h.hass, self.h.entry)
        h = await Harness(saved=self.h.hass.store.saved).setup()
        h.send(5250, retain=True)
        self.assertFalse(h.runtime['online'])
        self.assertEqual(h.runtime['last_reading'], last)
        self.assertAlmostEqual(calculations.volume(h.runtime['latest'],h.entry),4500)

    async def test_first_retained_payload_is_known_value_with_unknown_age(self):
        self.h.send(5000, retain=True)
        self.assertFalse(self.h.runtime['online'])
        self.assertIsNone(self.h.runtime['last_reading'])
        self.assertAlmostEqual(calculations.volume(self.h.runtime['latest'],self.h.entry),5000)

    async def test_telemetry_timeout_option_is_used(self):
        h = await Harness(telemetry_timeout=30).setup()
        h.send(4500)
        h.settle(20)
        self.assertTrue(h.runtime['online'])
        h.settle(11)
        self.assertFalse(h.runtime['online'])

    async def test_snapshot_omits_nonfinite_diagnostics_and_unknown_fields(self):
        import json
        self.h.send(payload={'voltage_mv':1200,'wifi_rssi':float('nan'),'unused':float('inf'),'firmware':'6.1.0'})
        saved = self.h.pending_data()
        json.dumps(saved, allow_nan=False)
        self.assertNotIn('wifi_rssi',saved['latest'])
        self.assertNotIn('unused',saved['latest'])


if __name__ == '__main__':
    unittest.main()
