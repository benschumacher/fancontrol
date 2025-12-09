# Raspberry Pi Fan Controller

## Introduction

This project provides a simple and effective way to control a fan connected to a Raspberry Pi's GPIO pins based on the CPU temperature. The script runs as a background service, automatically adjusting the fan speed to keep the CPU cool.

## Dependencies

*   RPi.GPIO
*   rpi_hardware_pwm

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd fancontrol
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
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

The script is configured via the `config.ini` file. If this file is not found, the script will run with a set of default values.

### [fan]
*   `pin`: The GPIO pin connected to the fan. Default: `12`
*   `pwm_freq`: The PWM frequency for the fan. Default: `100`
*   `wait_interval`: The interval in seconds between temperature checks. Default: `5`

### [temperature]
*   `thermal_file`: The file to read the CPU temperature from.
*   `target`: The target CPU temperature in Celsius.
*   `hysteresis`: The temperature hysteresis in Celsius to prevent rapid fan speed changes.

### [fan_curve]
The `curve` option defines the fan's speed at different temperatures. The script uses linear interpolation to determine the fan speed between these points. The format is a series of `temperature: duty_cycle` pairs, each on a new line.

Example:
```ini
[fan_curve]
curve =
    52: 50
    62: 75
    72: 100
```

## Discover Duty Cycle

The script includes a mode to help you determine the minimum duty cycle required to start your fan.

To use this tool, run the script with the `--discover-duty-cycle` flag:
```bash
python3 fancontrol.py --discover-duty-cycle
```
The script will prompt you to enter a duty cycle percentage (0-100). You can test different values to find the minimum value that reliably starts your fan.

## Fan Startup Considerations

Some fans require a higher initial PWM duty cycle to start spinning than they do to maintain speed. If you find that your fan is not starting when the temperature first crosses the threshold, you should determine the minimum starting duty cycle using the [Discover Duty Cycle](#discover-duty-cycle) tool and set the first point of your `fan_curve` to that value.

For example, if you find that your fan reliably starts at 60% duty cycle, you could set your `fan_curve` like this:
```ini
[fan_curve]
curve =
    52: 60  # Set the first point to the minimum startup duty cycle
    62: 75
    72: 100
```
This ensures the fan gets a sufficient "kick" to start spinning.
