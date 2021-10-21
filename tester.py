"""Make sure you adjust the contrast before you think it doesn't work."""
from simple_hd44780 import LCD
from simple_hd44780.interfaces import PCF8574I2CBackpackInterface

interface = PCF8574I2CBackpackInterface(0x27)

lcd = LCD(interface, lines=1, matrix_size=0)

# This is "one row" (16 chars).
lcd.write_char("A", 0)
lcd.write_char("B", 3)
# First char of second line.
lcd.write_char("s", 16)
lcd.write_char("?", 31)


# lcd.cursor_blinking_enabled = False
# lcd.write_char()
