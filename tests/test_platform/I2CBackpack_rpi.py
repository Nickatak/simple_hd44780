"""Tests for the I2C backpack interface on the raspberry pi.

    Pin layout: https://pinout.xyz/

    Hardware:
        1. Raspberry Pi B+
        2. 4 Jumper wires (1 SDA, 1 SCL, 1 Vcc, 1 GND)
        3. PCF8574 Serial Backpack
        4. HD44780 LCD

    For these tests, the following wires have been connected:
        1. `Raspberry Pi SDA (12C1)` GPIO/BCM pin 2; BOARD pin 3 -> PCF8574 SDA pin.
        2. `Raspberry Pi SCL (12C1)` GPIO/BCM pin 3; BOARD pin 5 -> PCF8574 SCL pin.
        3. `Raspberry Pi 5V pin` BOARD pin 4 -> PCF8574 Vcc pin.
        4. `Raspberry Pi Ground pin` BOARD pin 6 -> PCF8574 GND pin.
"""
