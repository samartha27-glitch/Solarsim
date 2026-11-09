
import unittest

from solar_sim import calculate_daily_load, calculate_system

class TestSolarSim(unittest.TestCase):

    def test_daily_load(self):
        loads = [
            {"count": 4, "watts": 5, "hours": 6},
            {"count": 1, "watts": 15, "hours": 6},
        ]
        self.assertAlmostEqual(calculate_daily_load(loads), 210)

    def test_panel_size(self):
        result = calculate_system(
            daily_load_wh=210,
            peak_sun_hours=4,
            performance_ratio=0.75,
            panel_size_w=100,
        )
        self.assertAlmostEqual(result.panel_size_w, 70)

    def test_two_day_battery_capacity(self):
        result = calculate_system(
            daily_load_wh=210,
            backup_days=2,
            depth_of_discharge=0.80,
            battery_efficiency=0.90,
            battery_voltage=12,
        )
        expected_wh = 210 * 2 / (0.80 * 0.90)
        self.assertAlmostEqual(result.battery_capacity_wh, expected_wh)
        self.assertAlmostEqual(
            result.battery_capacity_ah, expected_wh / 12
        )

    def test_zero_load(self):
        result = calculate_system(daily_load_wh=0)
        self.assertEqual(result.panel_size_w, 0)
        self.assertEqual(result.battery_capacity_wh, 0)

    def test_invalid_sun_hours(self):
        with self.assertRaises(ValueError):
            calculate_system(daily_load_wh=210, peak_sun_hours=0)

    def test_invalid_load_hours(self):
        loads = [{"count": 1, "watts": 5, "hours": 25}]
        with self.assertRaises(ValueError):
            calculate_daily_load(loads)

if __name__ == "__main__":
    unittest.main()