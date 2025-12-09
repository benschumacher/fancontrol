#!/usr/bin/env /home/pi/src/repos/fancontrol/env/bin/python3
import re
import sys

from abc import ABC
from time import sleep

import RPi.GPIO as GPIO
#from rpi_hardware_pwm import HardwarePWM

THERMAL_FILE = '/sys/class/thermal/thermal_zone0/temp'
FAN_PIN = 12                     # fan control PIN
PWM_FREQ = 100
WAIT = 5000
MIN_RPM = 1500
MAX_RPM = 5000
TEMP_TARGET = 51
HYSTERESIS = 0.5
MIN_CYCLES = 3
OUTPUT = sys.stdout if sys.stdout.isatty() else sys.stderr

# Set's GPIO pins to BCM GPIO numbering
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(FAN_PIN, GPIO.OUT)
fan = GPIO.PWM(FAN_PIN, PWM_FREQ)
fan.start(0)
fan.ChangeDutyCycle(0)

#fan = HardwarePWM(pwm_channel=0, hz=PWM_FREQ, chip=0)
#fan.start(0)
#fan.change_duty_cycle(0)


def main():
    dc = 0
    cycles = 0
    start_cycle = None

    try:
        while True:
            temp_current = None

            with open('/sys/class/thermal/thermal_zone0/temp') as f:
                temp_current = round(float(f.readline()) / 1000, 1)

            cycles += 1
            if not start_cycle or cycles > start_cycle:
                if dc == 0 and temp_current > TEMP_TARGET + HYSTERESIS:
                    # first startup goes to full speed
                    dc = 100
                    start_cycle = cycles
                else:
                    if round(temp_current) >= 70:
                        dc = 100
                    if 70 > round(temp_current) >= 66:
                        dc = 90
                    if 66 > round(temp_current) >= 60:
                        dc = 85
                    if 60 > temp_current:
                        dc = 66
                    if ((not start_cycle or (cycles - start_cycle) > MIN_CYCLES)
                        and TEMP_TARGET - HYSTERESIS > temp_current):
                        dc = 0

            if start_cycle and (cycles - start_cycle) > MIN_CYCLES:
                start_cycle = None

            fan.ChangeDutyCycle(dc)
            rpm = 0 if dc <= 0 else int(MAX_RPM * dc / 100)
            temp_delta = round(temp_current - TEMP_TARGET, 1)
            print(f"[PWM] Temp: {temp_current}"
                  f" | TempDelta: {temp_delta}"
                  f" | RPM: {rpm} (DC: {dc}%)"
                  f" | Cycles: {cycles}", file=sys.stderr)
            sleep(float(WAIT) / 1000)
    except KeyboardInterrupt:
        fan.stop()
        GPIO.cleanup()

    return 0


if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
