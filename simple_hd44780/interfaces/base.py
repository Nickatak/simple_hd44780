import time
from abc import ABCMeta


class BaseInterface(metaclass=ABCMeta):
    """ABC defining required methods for an LCD interface.

    An interface is defined as the "thing between the microcontroller and
    the LCD controller", regardless whether that "thing" is some kind of
    BUS or raw I/O pins.  Note: there is NO type checking/validation at this
    level (OTHER than normalizing to 1/0 with the bitwise AND).

    The relevant necessary pins to be controlled on the HD44780 are listed below:
        - RS
        - RW
        - E
        - A
        - D0 (Not necessary for 4-bit operation mode)
        - D1 (Not necessary for 4-bit operation mode)
        - D2 (Not necessary for 4-bit operation mode)
        - D3 (Not necessary for 4-bit operation mode)
        - D4
        - D5
        - D6
        - D7

    RS is the Register Select bit, HIGH for data input, LOW for instruction input; in
    short, this pin will be set to HIGH when you are doing data read/writes from the
    CGRAM/DDRAM and LOW at all other times.
    RW is the Read/Write bit, HIGH for read, LOW for write.  This pin is set to HIGH when
    you are reading data from the CGRAM/DDRAM or want to read the busy flag/address.
    E is the enable signal, pulse it to have the LCD read the set bits.  The pulse is
    LOW->HIGH->LOW, as the LCD controller looks for a falling-edge voltage pattern in
    order to rid the pins' states.
    A is the backlight-5V pin.  HIGH for on, LOW for off.  I hope this one is self explanatory,
    but just incase: HIGH to have the backlight on, LOW to have the backlight unpowered.  Do
    note that if you are manually testing this with an LED/multimeter/etc., you have to connect
    the A pin to the K ground in order to see it turn on/off.
    D0-D7 are data bits that indicate different things based upon the whole byte.

    When the interface is a 4-bit operational usage interface, it will need to split the D0-D7
    data bits into TWO E-pulses like so (keep in mind that only D4-D7 are actually used in 4-bit
    operational mode):
        1. Set D4-7 states with the high-nibble.
        2. Pulse E.
        3. Set D4-7 AGAIN with the states of the low-nibble.
        4. Pulse E.

        Example of four-bit operational command-sending:
            The command we want to send is ABCDEFGH (their states are arbitrary for this
            demonstration -- the letters are only there for positional reference).
            1. Set data pins:
                - D4: D
                - D5: C
                - D6: B
                - D7: A
            2. Pulse Enable pin:
                - Set Enable pin LOW
                - Set Enable pin HIGH
                - Set Enable pin LOW
            3. Set data pins:
                - D4: H
                - D5: G
                - D6: F
                - D7: E
            4. Pulse Enable pin:
                - Set Enable pin LOW
                - Set Enable pin HIGH
                - Set Enable pin LOW

    IMPORTANT: To limit the necessary libraries associated with this, make sure that you perform
    any platform-specific dependency imports (EG: Rpi.GPIO) INSIDE the interface's `__init__()` method.

    An interface must implement the following thing in order to be used by the LCD class:
        `_pulse_enable_signal()`
        `_set_data(byte)`
        `set_rs_state(state)`
        `set_rw_state(state)`
        `set_backlight_state(state)`
        `send_data(byte, delay=??)`
        `initialize(operation_mode, operation_mode, lines, matrix_size, memory_direction, display_shift)`
    """

    def delay(self, microseconds):
        """This is going to be useful during the initialization method."""
        time.sleep(microseconds / 1000000)

    def set_rs_state(self, state):
        """This must set the state of the RS pin to HIGH/LOW.

        Arguments:
            :state: Boolean/Integer - True/1 for HIGH, False/0 for LOW.
        """
        raise NotImplementedError

    def set_rw_state(self, state):
        """This must set the state of the RW pin to HIGH/LOW.

        Arguments:
            :state: Boolean/Integer - True/1 for HIGH, False/0 for LOW.
        """
        raise NotImplementedError

    def set_backlight_state(self, state):
        """This must set the state of the A pin to HIGH/LOW.

        Arguments:
            :state: Boolean/Integer - True/1 for HIGH, False/0 for LOW.
        """
        raise NotImplementedError

    def send_data(self, byte, delay=60):
        """This sends data to the LCD.

        This SHOULD deal with splitting data-bits for operation modes into appropriate packet
        sizes as well as pulsing the Enable pin so the LCD reads the set state.

        See the main docstring on the `BaseInterface` for more information regarding the differences
        between 4-bit/8-bit operational mode.

        Arguments:
            :byte: Byte/Integer - The bits representing a command for the LCD.
            :delay: Integer - after-command delay in microseconds.
        """
        raise NotImplementedError

    def _pulse_enable_signal(self):
        """Pulses the enable-signal pin with the pattern of LOW->HIGH->LOW."""
        raise NotImplementedError

    def _set_data(self, byte):
        """This is necessary to set all the data pins during the initialization sequence.

        This should NOT deal with splitting data-bits up for operation mode, and should
        only be used to set D7-D0 (High->Low) to the values of the specified byte.

        Arguments:
            :byte: Byte/Integer - The bits representing the states of the D7-D0 data pins.
        """
        raise NotImplementedError

    def _static_initialization(self):
        """This should handle the static initialization sequence specified by the data sheet."""

        self.set_rs_state(0)
        self.set_rw_state(0)

        self.delay(15000)
        # Static command of 00110000.
        self._set_data(0x30)
        self._pulse_enable_signal()

        self.delay(4100)
        # Static command of 00110000.
        self._set_data(0x30)
        self._pulse_enable_signal()

        self.delay(100)
        # Static command of 00110000.
        self._set_data(0x30)
        self._pulse_enable_signal()
        self.delay(100)

    def initialize(self, operational_mode, lines, matrix_size, increment_direction, display_shift):
        """This is the initialization sequence specified in the data sheet.

        After performing the static initialization sequence, the next byte you send determines the
        operational mode (See the Function Set command from the relevant commands section below):
            1. 0x3... for 8-bit operation, and you're going to need to attach the number of lines/matrix size
            to the lower-half of the nibble.
            2. 0x20 for 4-bit operation.

        After sending the byte above, all other following commands should be able to be sent with the `send_data()`
        implementation, as the LCD controller will be operating in your desired mode.

        Relevant commands:
            Function Set:
                This is a special command that is only used during initialization.  This particular command
                DOES have a different behavior depending upon what mode you intend to set.
                    - L: Set HIGH for 8-bit mode.  Set LOW for 4-bit mode.  Since this interface base class is
                    meant to be used in 4-bit operational mode (see Author's note at bottom).
                    - N: Set HIGH for 2 display lines.  Set LOW for 1 display line.
                    - F: Set HIGH for 5x10 character size.  Set LOW for 5x7 character size.  Note: Due
                    to the maximum size of the display, you can't run 2-lines with 5x10 size characters.

                For 8-bit operational mode:
                    Byte1:
                        Index: 76543210
                        Byte:  001LNFXX

                For 4-bit operational mode:
                    Byte1:
                        Index: 76543210
                        Byte:  001LXXXX
                    Byte2:
                        Index: 76543210
                        Byte:  NFXXXXXX

            Entry mode set:
                This is a special command to be used during the initalization phase only.  It sets the following
                two attributes:
                    - D: Set HIGH for increment-address as we move to the right (ex: romance languages) and LOW
                        to decrement the address as we move to the right (ex: Japanese, Hebrew, Arabic, etc.).
                    - S: Set HIGH to shift the display as the DDRAM is being written to (this makes it look as if
                    the cursor doesn't move); the shift-direction is dictated by the preceding D-option in this
                    command (1 shifts to the left, 0 to the right).  Set to LOW to disable display shifting.

                Data bits:
                        Index: 76543210
                        Byte:  000001DS

        Arguments:
            :operational_mode: Boolean/Integer - True/1 for 8-bit operational mode.  False/0 for 4-bit operational
            mode.
            :lines: Boolean/Integer - True/1 for 2 lines.  False/0 for 1 line.
            :matrix_size: Boolean/Integer - True/1 for 5x10 character size.  False/0 for 5x7 character size.
            :increment_direction: - Boolean/Integer - True/1 to increment as we move to the right.  False/0 to
            increment as we move to the left.
            :display_shift: - Boolean/Integer - True/1 to enable display-shifting.  False/0 to disable display-shifting.
        """
        self._static_initialization()

        function_set_command = 0x20
        entry_mode_set_command = 0x04
        if operational_mode:
            # For 8 bit operation.
            self._set_data(function_set_command | (operational_mode << 4) | (lines << 3) | (matrix_size << 2))
            self._pulse_enable_signal()
        else:
            # For 4 bit operation.
            self._set_data(function_set_command)
            self._pulse_enable_signal()
            self.delay(1000)

            self.send_data( function_set_command | (lines << 3) | (matrix_size << 2) )

        # Static byte.
        self.send_data(0x08)
        # Clear screen/return DDRAM address to 0 (home).
        self.send_data(0x01, delay=3000)
        self.send_data(entry_mode_set_command | (increment_direction << 1) | display_shift)
