"""Weather fallback, electrical preservation and refill artifact regressions."""
import unittest
from datetime import timedelta
from types import SimpleNamespace

from tests.support import Clock, Harness, calculations, integration
from custom_components.jojo_tank.compensation import apply_compensation


class CompensationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        Clock.reset()
        self.h = await Harness(temperature_compensation=True).setup()
        self.weather(35)

    def weather(self, temperature, unit='°C', age=0, state='sunny'):
        value = SimpleNamespace(state=state, attributes={'temperature':temperature, 'temperature_unit':unit}, last_updated=Clock.now-timedelta(minutes=age))
        self.h.hass.states = SimpleNamespace(get=lambda entity: value if entity=='weather.forecast_home' else None)

    def sample(self, depth=1755):
        p = {'current_raw_ma':4+depth/self.h.entry.data['tank_height']*7.5}
        apply_compensation(p, self.h.entry, self.h.hass, Clock.now)
        return p

    def test_trial_anchor_preserves_electrical_values(self):
        p = self.sample()
        self.assertAlmostEqual(calculations.raw_depth(p,self.h.entry),1755)
        self.assertEqual(p['_temperature_correction_mm'],75)
        self.assertAlmostEqual(calculations.depth(p,self.h.entry),1830)
        self.assertLess(abs(1830-1900)/1900,.05)
        # This one-point example is not a multi-temperature accuracy validation.
        self.assertAlmostEqual(calculations.current(p,self.h.entry),4+1755/self.h.entry.data['tank_height']*7.5)

    def test_invalid_stale_and_missing_weather_fall_back(self):
        for temperature, unit, age, state in [(35,'°C',121,'sunny'),(35,'°C',0,'unavailable'),('nan','°C',0,'sunny'),(46,'°C',0,'sunny'),(35,None,0,'sunny')]:
            self.weather(temperature,unit,age,state)
            self.assertEqual(self.sample()['_temperature_correction_mm'],0)
        self.h.hass.states = SimpleNamespace(get=lambda entity:None)
        self.assertEqual(self.sample()['_temperature_correction_mm'],0)

    def test_fahrenheit_and_bounds_and_empty(self):
        self.weather(95,'°F')
        self.assertEqual(self.sample()['_temperature_correction_mm'],75)
        self.weather(20)
        self.assertEqual(self.sample()['_temperature_correction_mm'],0)
        self.weather(40)
        self.assertEqual(self.sample()['_temperature_correction_mm'],75)
        self.assertEqual(self.sample(0)['_temperature_correction_mm'],0)
        self.h.entry.options['temperature_cap']=float('inf')
        self.assertEqual(self.sample()['_temperature_correction_mm'],0)

    def test_depth_above_full_and_volume_clamp(self):
        p=self.sample(1950)
        self.assertAlmostEqual(calculations.depth(p,self.h.entry),2025)
        self.assertEqual(calculations.level(p,self.h.entry),100)
        self.assertEqual(calculations.volume(p,self.h.entry),5250)

    async def test_weather_changes_cannot_create_refill_and_real_refill_works(self):
        for t in [20]*8+[35]*8+[20]*8+[35]*8:
            self.weather(t)
            self.h.send(4200)
        self.assertFalse(self.h.runtime['refilling'])
        self.assertEqual(self.h.runtime['refill_history'],[])
        for _ in range(6):
            self.weather(35)
            self.h.send(4700)
        self.assertTrue(self.h.runtime['refilling'])
        self.h.settle()
        self.assertEqual(self.h.runtime['refill_history'][0]['amount_l'],500)

    async def test_mqtt_cannot_inject_correction_and_reload_preserves_snapshot(self):
        self.weather(35)
        self.h.send(payload={'voltage_mv':1200,'_temperature_correction_mm':1000})
        p=self.h.runtime['latest']
        self.assertEqual(p['_temperature_correction_mm'],75)
        before=calculations.depth(p,self.h.entry)
        await integration.async_unload_entry(self.h.hass,self.h.entry)
        h=await Harness(saved=self.h.hass.store.saved,temperature_compensation=True).setup()
        self.assertAlmostEqual(calculations.depth(h.runtime['latest'],h.entry),before)
        self.assertFalse(h.runtime['online'])

    def test_disabled_default_uses_raw(self):
        self.h.entry.options['temperature_compensation']=False
        p=self.sample()
        self.assertEqual(p['_temperature_correction_mm'],0)
        self.assertAlmostEqual(calculations.depth(p,self.h.entry),1755)
