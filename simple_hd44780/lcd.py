class LCD:
    """HD44780 LCD class.

    The setting of pins to HIGH/LOW has been abstracted away into the interfaces (see
    the `interfaces.BaseInterface` for more information).

    Some basic/helpful terms:
        - DDRAM: Display-Data RAM, where the actual data mapped to the CGRAM/CGROM is stored.
        - CGROM: Character-Generation ROM, where "hard-coded" character maps reside (ex: ASCII
        chars).
        - CGRAM: Character-Generation RAM, where custom character maps are stored.

    Available commands:
        Bit legend:
            - X: Doesn't matter, can be set to anything.

        1. Clear the entire list and set DDRAM address to 0:
            RS: 0
            RW: 0
            Data bits:
                Index: 76543210
                Bits:  00000001

        2. Set DDRAM address to 0 (but doesn't clear the DDRAM):
            RS: 0
            RW: 0
            Data bits:
                Index: 76543210
                Bits:  0000001X

        3. Display toggle controls:
            This command toggles common display controls (display/cursor/blinking) listed below:
                - D: Set HIGH to turn the display on (  Set LOW to turn off he display.  Note: this is NOT the
                backlight; the backlight is controlled by the A pin above that is grounded to the K pin).
                - C: Set HIGH to show the cursor's current position on the display.  Set LOW to hide the cursor's
                current position on the display.
                - B: Set HIGH to have the cursor blink.  Set LOW to have the cursor stay solid.  If the previous C
                option is NOT HIGH, then this setting doesn't do anything immediately.

            RS: 0
            RW: 0
            Data bits:
                Index: 76543210
                Bits:  00001DCB

        4. Cursor/Display shift:
            This command moves the display or cursor to the left or right without altering the DDRAM.  Just like the
            set DDRAM Address's behavior, the "first row" of characters has 40 slots.  The cursor WILL move into the
            "second row" of characters after it passes said 40th character; however, the cursor will NOT move backwards
            into the "first row" from the second.
                - S: Set HIGH to shift the cursor. Set LOW to shift the display.
                - D: Set HIGH to shift to the right.  Set LOW to shift to the left.  WHAT this shifts is dependant
                upon the S-option previously set.

            RS: 0
            RW: 0
            Data bits:
                Index: 76543210
                Bits:  0001SDXX

        5. CGRAM Set:
            Need to document this later.

        6. DDRAM Set:
            This command sets the address pointer to the "display slot" for the future read/write operations.
                - The 7 bits of A make up an integer that corresponds to the address of the character-slot. Ex:
                    0000101 => 5 (or the 6th character slot, the memory address is 0-indexed)

                It should be noted that the display's maximum-character on the first line is at 0x27 (39).  The
                offset for the second line starts at 0x40 (64).  Note: for 4-line displays that only have 20 chars
                per line, the memory is split in such a way that the odd-paired lines share a singular line's memory,
                making the first line 0x00->0x13, the second line 0x40->0x53, the third line 0x14->0x27. and the
                fourth line from 0x54->0x67.

            RS: 0
            RW: 0
            Data bits:
                Index: 76543210
                Bits:  1AAAAAAA
    """

    def __init__(
        self,
        interface,
        lines=1,
        matrix_size=0,
        backlight_enabled=True,
        cursor_enabled=True,
        display_enabled=True,
        cursor_blinking_enabled=True,
        skip_setup=False,
    ):
        """Creates a new LCD controller.

        Available getters/setters:
            backlight_enabled - True/False
            display_enabled - True/False
            cursor_enabled - True/False
            cursor_blinking_enabled - True/False

        Easy usage:
            1. Pick an interface.
            2. Make your interface: `interface = PCF8574I2CBackpackInterface()`.
            3. Initialize the lcd: `lcd = LCD(interface)`.
            4. Done, control your LCD however you see fit.


        Arguments:
            :interface: BaseInterface child class - the "hardware" interface to use.
            :lines: Integer - How many lines you want your LCD to use.  Options: [1,
            2, 4]
            :matrix_size: Boolean/Integer - True/1 for 5x10 matrix-size per char.  Fa-
            lse/0 for 5x7 matrix-size per char.
        """

        self.interface = interface
        if not skip_setup:
            self.interface.initialize(
                operational_mode = 0,
                lines = 1,
                matrix_size = 0,
                increment_direction = 1,
                display_shift = 0,
            )

        # It doesn't matter what the values are, as they'll be overwritten shortly.
        self._backlight_enabled = False
        self._cursor_enabled = False
        self._cursor_blinking_enabled = False

        self.backlight_enabled = backlight_enabled
        self.display_enabled = display_enabled
        self.cursor_enabled = cursor_enabled
        self.cursor_blinking_enabled = cursor_blinking_enabled


    def write_text(self, text, index=None):
        if index is not None:
            pass # DDRAM shift before writing the text.


    def write_char(self, char, index=None):
        if index is not None:
            pass # DDRAM shift before writing char.
        self.interface.set_rs_state(1)
        self.interface.send_data(ord(char))
        self.interface.set_rs_state(0)

    @property
    def backlight_enabled(self):
        return self._backlight_enabled

    @backlight_enabled.setter
    def backlight_enabled(self, state):
        self.interface.set_backlight_state(state)
        self._backlight_enabled = state

        return self._backlight_enabled

    @property
    def display_enabled(self):
        return self._display_enabled

    @display_enabled.setter
    def display_enabled(self, state):
        self.interface.send_data(0x08 | (state & 1) << 2)
        self._display_enabled = state

        return self._display_enabled

    @property
    def cursor_enabled(self):
        return self._cursor_enabled

    @cursor_enabled.setter
    def cursor_enabled(self, state):
        self.interface.send_data(0x08 | self._display_enabled << 2 | (state & 1) << 1)
        self._cursor_enabled = state

        return self._cursor_enabled

    @property
    def cursor_blinking_enabled(self):
        return self._cursor_blinking_enabled

    @cursor_blinking_enabled.setter
    def cursor_blinking_enabled(self, state):
        self.interface.send_data(0x08 | self._display_enabled << 2 | self._cursor_enabled << 1 | (state & 1))
        self._cursor_blinking_enabled = state

        return self._cursor_blinking_enabled
