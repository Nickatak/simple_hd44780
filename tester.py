"""Make sure you adjust the contrast before you think it doesn't work."""
from simple_hd44780 import LCD
from simple_hd44780.interfaces import PCF8574I2CBackpackInterface

interface = PCF8574I2CBackpackInterface(0x27)
lcd = LCD(interface)

#cd.clear()
#lcd.write_char()
lcd.write_char("H")