from simple_hd44780.interfaces.base import BaseInterface


class PCF8574I2CBackpackInterface(BaseInterface):
    """Interface for the I2C backpack with the PCF8574 8-bit I/O expander to drive the
    HD44780 LCD in 4-bit operation mode.

    The way that the PCF8574 LCD Backpack is wired is a not-straightforward; since
    it is an I2C-bus (serial-type connection) you can only write one byte at a time
    to it, thus the byte has 8 positions (4 bits for the RS/RW/E/A and 4 bits for the
    data).  If your backpack is wired differently, you may have to change around the
    pins to their corresponding bits, but as an added bonus, this should work with ANY
    PCF8574 I2C backpack.
    """

    def __init__(
        self,
        i2c_addr=0x27,
        rs_bit=0,
        rw_bit=1,
        e_bit=2,
        a_bit=3,
        data_bits=[4, 5, 6, 7],
        i2c_peripherals=1,
        pre_configured_byte=0,
    ):
        """Creates a new PCF8574I2CBackpackInterface object.

        Arguments:
            :addr: Byte/Integer - address for the I2C device.
            :rs_bit: Integer - Bit position for the RS bit.
            :rw_bit: Integer - Bit position for the RW bit.
            :e_bit: Integer - Bit position for the E bit.
            :a_bit: Integer - Bit position for the A bit.
            :data_bits: List[Integers] - Bit positions for the data bits. Index 0 in the list corresponds
            to the D4 pin, index 1 to the D5 pin, and so on respectively.
            :i2c_peripherals: Integer - A specifier for which set of I2C peripherals you're using.
            If you have more I2C interfaces, they'd be enumerated, I think (need more clarification?).
            :pre_configured_byte: Byte - Initial state of the control desired.
        """
        import smbus

        self.bus = smbus.SMBus(i2c_peripherals)
        self.i2c_addr = i2c_addr

        self.rs_bit_pos = rs_bit
        self.rw_bit_pos = rw_bit
        self.e_bit_pos = e_bit
        self.a_bit_pos = a_bit
        self.data_bit_pos = data_bits

        self._byte = pre_configured_byte
        self._write()

    def writes_byte(func):
        """Decorator helper to write the byte after the function ends.

        Note: This wrapper writes the current byte to the PCF8574, NOT to the LCD.  In
        order to get the LCD to read the set-bits, we have to pulse the E pin (see
        the `interfaces.BaseInterface` class for more information).

        Used for:
            set_rs_bit()
            set_rw_bit()
            pulse_enable_signal()
        """

        def wrapped(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self._write()

        return wrapped

    @writes_byte
    def set_rs_state(self, state):
        """Sets the RS bit to a given state.

        See the `interface.BaseInterface` for more details about the pin.

        Arguments:
            :state: Boolean/Integer - True/1 to set the bit to 1.  False/0 to set
            the bit to 0.
        """

        self._set_bit(self.rs_bit_pos, state & 1)

    @writes_byte
    def set_rw_state(self, state):
        """Sets the RW bit to a given state.

        See `interfaces.BaseInterface` for more details about the pin.

        Arguments:
            :state: Boolean/Integer - True/1 to set the bit to 1.  False/0 to set
            the bit to 0.
        """

        self._set_bit(self.rw_bit_pos, state & 1)

    @writes_byte
    def set_backlight_state(self, state):
        """Sets the backlight bit to a given state.

        See `interfaces.BaseInterface` for more details about the pin.

        Arguments:
            :state: Boolean/Integer - True/1 to set the bit to 1.  False/0 to set
            the bit to 0.
        """

        self._set_bit(self.a_bit_pos, state & 1)

    @writes_byte
    def _pulse_enable_signal(self):
        """Pulses the E bit in the following pattern LOW->HIGH->LOW.

        The third `_write` is handled by the writes_byte decorator.  See
        `interfaces.BaseInterface` for more details about the pin.


        """
        self._set_bit(self.e_bit_pos, 0)
        self._write()
        self.delay(1)
        self._set_bit(self.e_bit_pos, 1)
        self._write()
        self.delay(1)
        self._set_bit(self.e_bit_pos, 0)

    def send_data(self, byte, delay=60):
        """Sets the 4 data bits to the ones given in the nibble.

        We use the mask to take the higher-4 bits of the nibble, as well
        as the lower-4 bits of our current byte (the RS/RW/E/A bits).  We
        simply shift the data bits to where we want them and perform a
        bitwise OR to combine them together, and then set it back into
        our current byte for writing to the bus.  We then pulse so the LCD
        will read our set-data bits.

        Argument:
            :byte: Byte/Integer - This is the data we want to send.
            :is_nibble: Boolean - True to only send one nibble.  False
            to send a "packet" (two nibbles, AKA a singular byte).
            :delay: Integer - After-command delay amount in micro-seconds.
        """

        conf_bits = 0x0F & self._byte
        data_bits = 0xF0 & byte
        # Send the higher 4 bits first.
        self._byte = data_bits | conf_bits
        self._write()
        self._pulse_enable_signal()

        # Send the lower 4 bits in another byte.
        data_bits = (0x0F & byte) << 4

        self._byte = data_bits | conf_bits
        self._write()
        self._pulse_enable_signal()

        self.delay(delay)

    @writes_byte
    def _set_data(self, byte):
        """Only sets the data bits from the byte.

        Uses a mask to take the upper-bits and uses them as the data bits.  Since
        the PCF8574 is an 8 bit expander and the 4 bits are already in use, we
        can only write a nibble.

        Arguments:
            :byte: Byte - The byte containing the upper-bits you want to use.
        """

        for i in range(4):
            pos = 7 - i
            self._set_bit(pos, (byte >> pos) & 1)


    def _set_bit(self, pos, val):
        """Sets a bit at a specific position to a specific value.

        The position is 0-based and assumes that a byte is in Most-Significant-Bit
        -First order.  Visual representation below:
            bits:  00000000
            index: 76543210

        Arguments:
            :pos: Integer - The 0-based index of the bit you want to set.
            :val: Boolean - The value you want to set.
        """

        if val:
            self._byte |= 1 << pos
        else:
            self._byte &= ~(1 << pos)

    def _write(self):
        """Writes the current bit-state to the PCF8574.

        Note: This function writes to the PCF8574 only, it does NOT write
        to the LCD (that is achieved through pulsing the e_bit).
        """

        self.bus.write_byte(self.i2c_addr, self._byte)
        self.delay(1)
