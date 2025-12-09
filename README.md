# Raspberry Pi Fan Controller

## Introduction

This project provides a simple and effective way to control a fan connected to a Raspberry Pi's GPIO pins based on the CPU temperature. The script runs as a background service, automatically adjusting the fan speed to keep the CPU cool.

## Dependencies

*   [RPi.GPIO](https://pypi.org/project/RPi.GPIO/)
*   [rpi-hardware-pwm](https://pypi.org/project/rpi-hardware-pwm/) (optional, commented out by default)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd fancontrol
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install the service:**
    ```bash
    sudo cp service/fancontrol.service /etc/systemd/system/
    sudo systemctl enable fancontrol.service
    sudo systemctl start fancontrol.service
    ```

## Usage

The fan controller runs as a background service. You can check its status with:

```bash
sudo systemctl status fancontrol.service
```

The script will automatically adjust the fan speed based on the CPU temperature.

## Configuration

The script can be configured by editing the constants at the top of the `fancontrol.py` file:

*   `THERMAL_FILE`: The file to read the CPU temperature from.
*   `FAN_PIN`: The GPIO pin connected to the fan.
*   `PWM_FREQ`: The PWM frequency for the fan.
*   `WAIT`: The interval in milliseconds between temperature checks.
*   `MIN_RPM`, `MAX_RPM`: The minimum and maximum RPM of the fan (used for logging).
*   `TEMP_TARGET`: The target CPU temperature in Celsius.
*   `HYSTERESIS`: The temperature hysteresis in Celsius to prevent rapid fan speed changes.
*   `MIN_CYCLES`: The minimum number of cycles before the fan can be turned off.
