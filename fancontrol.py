#!/usr/bin/env python3
from time import sleep           # Allows us to call the sleep function to slow down our loop
import RPi.GPIO as GPIO          # Allows us to call our GPIO pins and names it just GPIO
import subprocess
 
THERMAL_FILE = '/sys/class/thermal/thermal_zone0/temp'
FAN_PIN = 12                     # fan control PIN
PWM_FREQ = 768
WAIT = 5000
MIN_RPM = 1500
MAX_RPM = 5000
TEMP_TARGET = 51

GPIO.setmode(GPIO.BCM)           # Set's GPIO pins to BCM GPIO numbering
GPIO.setup(FAN_PIN, GPIO.OUT)
fan = GPIO.PWM(FAN_PIN, PWM_FREQ)
fan.start(0)

dc = 0
try:
    while True:
        temp_current = None

        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            temp_current = round(float(f.readline()) / 1000, 1)

        if dc == 0 and temp_current > TEMP_TARGET:
            # first startup goes to full speed
            dc = 100
        else:
            if round(temp_current) >= 70:
                dc = 100
            if 70 > round(temp_current) >= 60:
                dc = 85 
            if 60 > temp_current >= TEMP_TARGET:
                dc = 66
            else:
                dc = 0

        fan.ChangeDutyCycle(dc)
        rpm = 0 if dc <= 0 else int(MAX_RPM * dc / 100)
        temp_delta = round(temp_current - TEMP_TARGET, 1)
        print(f"[PWM] Temp: {temp_current} | TempDelta: {temp_delta} | RPM: {rpm} (DC: {dc}%)")
        sleep(float(WAIT) / 1000)
except KeyboardInterrupt:
    fan.stop()
    GPIO.cleanup()

