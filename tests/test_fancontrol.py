import sys
import unittest
from unittest.mock import patch, mock_open, MagicMock
import os

# Directly mock RPi.GPIO in sys.modules BEFORE any other imports that might depend on it
sys.modules['RPi'] = MagicMock()
sys.modules['RPi.GPIO'] = MagicMock()

# Add the parent directory to sys.path to allow importing fancontrol.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fancontrol import FanController

class TestFanController(unittest.TestCase):

    def setUp(self):
        # Create a mock config.ini content
        mock_config_content = """
        [fan]
        pin = 12
        pwm_freq = 100
        wait_interval = 1
        min_rpm = 1500
        max_rpm = 5000

        [temperature]
        thermal_file = /sys/class/thermal/thermal_zone0/temp
        target = 50
        hysteresis = 2.0
        min_cycles = 3

        [fan_curve]
        curve =
            52: 50
            62: 75
            72: 100
        """
        # Patch os.path.exists and builtins.open to provide our mock content
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=mock_config_content)):
            self.controller = FanController(config_path='mock_config.ini')
        
        # Reset internal state for each test
        self.controller.dc = 0
        self.controller.cycles = 0
        self.controller.start_cycle = None

    def test_fan_off_below_hysteresis(self):
        self.controller.dc = 50 # Assume fan was on
        self.assertEqual(self.controller.calculate_duty_cycle(47.9), 0) # 47.9 < 50 - 2.0

    def test_fan_on_above_hysteresis(self):
        self.controller.dc = 0
        self.assertEqual(self.controller.calculate_duty_cycle(52.1), 50) # 52.1 > 50 + 2.0, should be at least 50

    def test_fan_speed_interpolation(self):
        self.controller.dc = 50 # Fan is on
        # Halfway between (52, 50) and (62, 75) -> should be 62.5, which rounds to 62
        self.assertEqual(self.controller.calculate_duty_cycle(57.0), 62)
        # 75% of the way between (62, 75) and (72, 100) -> 75 + 0.75 * 25 = 93.75, rounded to 94
        self.assertEqual(self.controller.calculate_duty_cycle(69.5), 94)

    def test_fan_speed_at_curve_points(self):
        self.controller.dc = 50 # Fan is on
        self.assertEqual(self.controller.calculate_duty_cycle(52.0), 50)
        self.assertEqual(self.controller.calculate_duty_cycle(62.0), 75)
        self.assertEqual(self.controller.calculate_duty_cycle(72.0), 100)
    
    def test_fan_speed_outside_curve(self):
        self.controller.dc = 50 # Fan is on
        # Below first point
        self.assertEqual(self.controller.calculate_duty_cycle(51.0), 50) # Should be 50 because it's the first point
        # Above last point
        self.assertEqual(self.controller.calculate_duty_cycle(75.0), 100)

    def test_hysteresis_band(self):
        # Fan is on, temp drops into hysteresis band -> should stay on
        self.controller.dc = 50
        self.assertEqual(self.controller.calculate_duty_cycle(49.0), 50) # 48 < 49 < 52
        
        # Fan is off, temp rises into hysteresis band -> should stay off
        self.controller.dc = 0
        self.assertEqual(self.controller.calculate_duty_cycle(51.0), 0) # 48 < 51 < 52

    def test_missing_config_file_uses_defaults(self):
        # Patch os.path.exists to return False
        with patch('os.path.exists', return_value=False):
            controller = FanController(config_path='non_existent_config.ini')
            # Assert that the controller is initialized with default values
            self.assertEqual(controller.fan_pin, 12)
            self.assertEqual(controller.temp_target, 51)

if __name__ == '__main__':
    unittest.main()
