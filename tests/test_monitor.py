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

    async def test_single_spike_and_sub_floor_recovery_are_rejected(self):
        self.warm()
        self.h.send(5250)
        for volume in [4500] * 6 + [4650] * 12:
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
            self.h.send(5000)
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


if __name__ == '__main__':
    unittest.main()
