#!/usr/bin/env python3
import re
import sys
import configparser
import logging
from time import sleep
import os
import argparse

try:
    import RPi.GPIO as GPIO
except ImportError:
    # Create a mock GPIO object if RPi.GPIO is not available
    # This allows the script to be imported and tested on non-Raspberry Pi devices
    class MockGPIO:
        BCM = None
        OUT = None
        def setmode(self, mode): pass
        def setwarnings(self, flag): pass
        def setup(self, pin, direction): pass
        def PWM(self, pin, freq): return self._MockPWM()

        class _MockPWM:
            def __init__(self): pass
            def start(self, dc): pass
            def ChangeDutyCycle(self, dc): pass
            def stop(self): pass
    
    GPIO = MockGPIO()
    logging.warning("RPi.GPIO not found. Running in mock GPIO mode.")

class FanController:
    def __init__(self, config_path='config.ini'):
        self.config = configparser.ConfigParser()
        # Set default values
        self.config['fan'] = {
            'pin': '12',
            'pwm_freq': '100',
            'wait_interval': '5',
            'min_rpm': '1500',
            'max_rpm': '5000'
        }
        self.config['temperature'] = {
            'thermal_file': '/sys/class/thermal/thermal_zone0/temp',
            'target': '51',
            'hysteresis': '2.0',
            'min_cycles': '3'
        }
        self.config['fan_curve'] = {
            'curve': '52: 50\n62: 75\n72: 100'
        }

        # Logging setup
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        if os.path.exists(config_path):
            self.config.read(config_path)
            logging.info(f"Loading configuration from {config_path}")
        else:
            logging.warning(f"Configuration file not found at {config_path}. Using default values.")

        # Fan configuration
        self.fan_pin = self.config.getint('fan', 'pin')
        self.pwm_freq = self.config.getint('fan', 'pwm_freq')
        self.wait_interval = self.config.getint('fan', 'wait_interval')
        self.min_rpm = self.config.getint('fan', 'min_rpm')
        self.max_rpm = self.config.getint('fan', 'max_rpm')

        # Temperature configuration
        self.thermal_file = self.config.get('temperature', 'thermal_file')
        self.temp_target = self.config.getfloat('temperature', 'target')
        self.hysteresis = self.config.getfloat('temperature', 'hysteresis')
        self.min_cycles = self.config.getint('temperature', 'min_cycles')

        # Fan curve
        self.fan_curve = []
        curve_string = self.config.get('fan_curve', 'curve').strip()
        if curve_string:
            for pair in curve_string.split('\n'):
                pair = pair.strip()
                if pair:
                    temp_str, dc_str = pair.split(':')
                    self.fan_curve.append((int(temp_str.strip()), int(dc_str.strip())))
        self.fan_curve.sort()

        # GPIO setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.fan_pin, GPIO.OUT)
        self.fan = GPIO.PWM(self.fan_pin, self.pwm_freq)
        self.fan.start(0)
        self.fan.ChangeDutyCycle(0)

        self.dc = 0
        self.cycles = 0
        self.start_cycle = None

    def get_cpu_temperature(self):
        try:
            with open(self.thermal_file) as f:
                return round(float(f.readline()) / 1000, 1)
        except (IOError, ValueError) as e:
            logging.error(f"Error reading temperature: {e}")
            return None

    def calculate_duty_cycle(self, temp):
        if temp is None:
            return self.dc # Keep last known duty cycle

        # OFF condition
        if temp < self.temp_target - self.hysteresis:
            return 0

        # ON condition (or speed change)
        if temp > self.temp_target + self.hysteresis:
            # If fan curve is not defined, or has less than 2 points, return 100%
            if not self.fan_curve or len(self.fan_curve) < 2:
                return 100
                
            # If temp is below the first point in the curve, use the first point's speed
            if temp <= self.fan_curve[0][0]:
                return self.fan_curve[0][1]
            
            # If temp is above the last point in the curve, use the last point's speed
            if temp >= self.fan_curve[-1][0]:
                return self.fan_curve[-1][1]

            # Find the two points to interpolate between
            for i in range(len(self.fan_curve) - 1):
                p1 = self.fan_curve[i]
                p2 = self.fan_curve[i+1]
                if p1[0] <= temp <= p2[0]:
                    # Linear interpolation formula
                    # y = y1 + (x - x1) * (y2 - y1) / (x2 - x1)
                    temp_range = p2[0] - p1[0]
                    dc_range = p2[1] - p1[1]
                    if temp_range == 0:
                        return p1[1]
                    
                    interpolated_dc = p1[1] + (temp - p1[0]) * dc_range / temp_range
                    return int(round(interpolated_dc))
        
        # If inside the hysteresis band, maintain current state
        return self.dc


    def run(self):
        try:
            while True:
                temp_current = self.get_cpu_temperature()
                if temp_current is not None:
                    self.cycles += 1
                    new_dc = self.calculate_duty_cycle(temp_current)

                    if new_dc != self.dc:
                        if self.dc == 0 and new_dc > 0:
                            self.start_cycle = self.cycles
                        self.dc = new_dc
                        self.fan.ChangeDutyCycle(self.dc)
                        logging.info(f"Fan speed changed to {self.dc}%")


                    if self.start_cycle and (self.cycles - self.start_cycle) > self.min_cycles:
                        self.start_cycle = None

                    rpm = 0 if self.dc <= 0 else int(self.max_rpm * self.dc / 100)
                    temp_delta = round(temp_current - self.temp_target, 1)
                    logging.info(f"Temp: {temp_current}°C | TempDelta: {temp_delta}°C | RPM: {rpm} (DC: {self.dc}%)")

                sleep(self.wait_interval)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        logging.info("Stopping fan controller.")
        self.fan.stop()
        GPIO.cleanup()

def discover_duty_cycle(config_path='config.ini'):
    # This function is intended to be run on a Raspberry Pi to test the fan.
    config = configparser.ConfigParser()
    config['fan'] = {'pin': '12', 'pwm_freq': '100'}
    if os.path.exists(config_path):
        config.read(config_path)
    
    fan_pin = config.getint('fan', 'pin')
    pwm_freq = config.getint('fan', 'pwm_freq')

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(fan_pin, GPIO.OUT)
    fan = GPIO.PWM(fan_pin, pwm_freq)
    fan.start(0)

    print("--- Fan Analyzer ---")
    print("Enter a duty cycle (0-100) to test the fan.")
    print("Enter 'q' to quit.")

    try:
        while True:
            dc_input = input("Duty Cycle: ")
            if dc_input.lower() == 'q':
                break
            
            try:
                dc = int(dc_input)
                if 0 <= dc <= 100:
                    fan.ChangeDutyCycle(dc)
                    print(f"Fan speed set to {dc}%")
                else:
                    print("Invalid input. Please enter a value between 0 and 100.")
            except ValueError:
                print("Invalid input. Please enter a number or 'q'.")

    except KeyboardInterrupt:
        pass
    finally:
        print("\nStopping fan and cleaning up GPIO.")
        fan.stop()
        GPIO.cleanup()

def main():
    parser = argparse.ArgumentParser(description="A script to control a cooling fan for a Raspberry Pi.")
    parser.add_argument('--discover-duty-cycle', action='store_true', help='Run a tool to discover the minimum duty cycle to start the fan.')
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(script_dir, 'config.ini')

    if args.discover_duty_cycle:
        discover_duty_cycle(config_path=config_path)
    else:
        controller = FanController(config_path=config_path)
        controller.run()


if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
