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
        lines=2,
        matrix_size=0,
        default_text="",
        backlight_enabled=True,
        cursor_enabled=True,
        display_enabled=True,
        cursor_blinking_enabled=True,
        skip_setup=False,
        operational_mode=0,
        increment_direction=True,
        display_shifting=False,
    ):
        """Creates a new LCD controller.

        Available getters/setters:
            `text` - String representation of current display-text; this can be used
            to set the display text as well.
            `backlight_enabled` - True/False for on/off respectively.
            `display_enabled` - True/False for on/off respectively.
            `cursor_enabled` - True/False for on/off respectively.
            `cursor_blinking_enabled` - True/False for on/off respectively.
            `lines` - How many lines your display is using.  There is no setter for this
            property, only a getter.
            `max_index` - Maximum index of the display in its current operating mode.  The-
            re is no setter for this property, only a getter.

        Available API:
            `.write_text(text, start_index)`
            `.write_char(char, index)`
            `.clear()`
            `.set_cursor(index)`

        Easy usage:
            1. Pick an interface.
            2. Make your interface: `interface = PCF8574I2CBackpackInterface()`.
            3. Initialize the lcd: `lcd = LCD(interface)`.
            4. Done, control your LCD however you see fit.

        Arguments:
            :interface: BaseInterface child class - the "hardware" interface to use.
            :lines: Integer - How many lines you want your LCD to use.
            False for 1 line.  Will think about adding 4-line support shortly.
            :matrix_size: Boolean/Integer - True/1 for 5x10 matrix-size per char.  Fa-
            lse/0 for 5x7 matrix-size per char.
            :default_text: String - Default text to be written to the display.
            :backlight_enabled: Boolean - Default state of the backlight.  True for on,
            False for off.
            :display_enabled: Boolean - Default state of the display.  True show the display,
            False to turn it off (Note: this is NOT the backlight).
            :cursor_enabled: Boolean - Default state of the cursor being shown.  True to
            show the cursor, False to hide it.
            :cursor_blinking_enabled: Boolean - Default state of the cursor blinking.  True to
            have the cursor blink, False to have it stay solid.
            :skip_setup: Boolean - Whether or not to run the the initialization routine for
            the HD44780.  True to skip the initialization routine (perhaps for connecting to an
            already-initialized display), False to perform initialization.
            :operational_mode: Boolean - 4-bit/8-bit operation mode toggle.  True for 8-bit opera-
            tion mode, False for 4-bit operation mode.
            :increment_direction: Boolean - Direction the DDRAM address increments.  True for right,
            False for left.
            :display_shift: Boolean - Enables/disables display-shifting.  True for on, False for off.
        """

        self.interface = interface
        if not skip_setup:
            self.interface.initialize(
                operational_mode=operational_mode,
                lines=lines,
                matrix_size=matrix_size,
                increment_direction=increment_direction,
                display_shift=display_shifting,
            )

        self._lines = lines
        self.max_index = self._get_max_index()
        self._max_len = self.max_index + 1
        self._curr_index = 0

        # It doesn't matter what the values are, as they'll be overwritten shortly.
        self._backlight_enabled = False
        self._display_enabled = False
        self._cursor_enabled = False
        self._cursor_blinking_enabled = False
        self._text = self._get_init_text(default_text="")

        self.backlight_enabled = backlight_enabled
        self.display_enabled = display_enabled
        self.cursor_enabled = cursor_enabled
        self.cursor_blinking_enabled = cursor_blinking_enabled

    def write_text(self, text, start_index=None):
        """Writes the given text to the LCD.

        Arguments:
            :text: String - The text to write to the LCD.
            :start_index: Integer/None - Optional specifier to the index to start
            writing at.  Note: index 16 is the first-character slot of the 2nd line.
        """

        if start_index is not None:
            self.set_cursor(start_index)

        for char in text:
            self.write_char(char)

    def write_char(self, char, index=None):
        """writes a singular character to the LCD.

        Arguments:
            :char: String - The singular character to write to the LCD.
            :start_index: Integer/None - Optional specifier to the index to start
            writing at.  Note: index 16 is the first-character slot of the 2nd line.
        """
        if index is not None:
            self.set_cursor(index)

        self.interface.set_rs_state(1)
        self.interface.send_data(ord(char))
        self.interface.set_rs_state(0)
        self._curr_index += 1

    def clear(self):
        """Clears the DDRAM entirely and sets the DDRAM address to 0 (first character slot).

        This also clears the `text` attribute.  The data byte is always going to be 0x01 for this command.
        There is an extensive delay for this command (~2ms).
        """
        self._text = ""
        self._curr_index = 0

        self.interface.send_data(0x01, delay=3000)

    def set_cursor(self, index):
        """Sets the cursor to the specified index.

        Note: If you have the cursor enabled, it WILL move the cursor block onto the index specified.
        If you have cursor blinking disabled, it will appear as a solid underscore underneath the
        character.

        If the index is 0, we can use command #2.
            Command 2. Set DDRAM address to 0 (but doesn't clear the DDRAM):
                RS: 0
                RW: 0
                Data bits:
                    Index: 76543210
                    Bits:  0000001X

        If the index is something else other than that, we're going to have to calculate where it should go.
        See `_convert_index_to_mem_addr(index)` for more info.

        Argument:
            :index: Integer - The 0-based index where you want to set the cursor to.
        """
        if index == 0:
            self.interface.send_data(0x02)
            self._curr_index = 0

        addr = self._convert_index_to_mem_addr(index)
        data = self._build_set_ddram_command(addr)
        self._curr_index = index

        self._curr_index = 0
        self.interface.send_data(data)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text):
        if len(new_text) + len(self.text) > self.max_index:
            pass

        self.clear()
        self.write_text(new_text)

    @property
    def lines(self):
        return self._lines

    @property
    def backlight_enabled(self):
        return self._backlight_enabled

    @backlight_enabled.setter
    def backlight_enabled(self, state):
        self._backlight_enabled = state
        self.interface.set_backlight_state(state)

        return self._backlight_enabled

    @property
    def display_enabled(self):
        return self._display_enabled

    @display_enabled.setter
    def display_enabled(self, state):
        self._display_enabled = state

        data = self._build_toggle_command()
        self.interface.send_data(data)

        return self._display_enabled

    @property
    def cursor_enabled(self):
        return self._cursor_enabled

    @cursor_enabled.setter
    def cursor_enabled(self, state):
        self._cursor_enabled = state

        data = self._build_toggle_command()
        self.interface.send_data(data)

        return self._cursor_enabled

    @property
    def cursor_blinking_enabled(self):
        return self._cursor_blinking_enabled

    @cursor_blinking_enabled.setter
    def cursor_blinking_enabled(self, state):
        self._cursor_blinking_enabled = state

        data = self._build_toggle_command()
        self.interface.send_data(data)

        return self._cursor_blinking_enabled

    def _build_toggle_command(self):
        """Builds the display-toggle controls data byte.

        Command 3. Display toggle controls:
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
        """

        return 0x08 | self._display_enabled << 2 | self._cursor_enabled << 1 | (self._cursor_blinking_enabled & 1)

    def _build_set_ddram_command(self, addr):
        """Builds the set-address pointer data byte.

        The address passed to this function ideally would be a returned value from `lcd._convert_index_to_mem_addr()`.

        Command 6. DDRAM Set:
            This command sets the address pointer to the "display slot" for the future read/write operations.
                - The 7 bits of A make up an integer that corresponds to the address of the character-slot. Ex:
                    0000101 => 5 (or the 6th character slot, the memory address is 0-indexed)

            RS: 0
            RW: 0
            Data bits:
                Index: 76543210
                Bits:  1AAAAAAA

        Arguments:
            :addr: Byte - address that you want to set the value to (max: 7 bits).
        """

        return 0x80 | addr

    def _get_max_index(self):
        if self._lines >> 1:
            # Then we know we have two lines.
            return 31
        else:
            return 15

    def _get_init_text(self, default_text):
        """Builds a usable List to hold characters in.

        I know that this:
            1. Isn't great for memory, but it's < 1kb, honestly, I think if this is substantial, you should
            probably use a lower level language anyway.
            2. Is a bit messy, but it will make the user's life easier, since they won't have to muck about with
            addresses, they can simply just use an index to specify where their cursor should be.
        """
        # TODO: Read all chars from DDRAM? Do I want to do that? Or just force-initialize?  Let's see how the
        # performance is with reading all the chars first.

    def _convert_index_to_mem_addr(self, index):
        """Converts an index to a memory address.

        This allows us to normalize the interface, for example, if I wanted to set/read `text[17]`, this would be
        the second character on line 2.  The memory is offset inside the HD47780 so I need to account for this
        when setting the DDRAM address.

        It should be noted that the display's maximum-character on the first line is at 0x27 (39).  The
        offset for the second line starts at 0x40 (64).  Note: for 4-line displays that only have 20 chars
        per line, the memory is split in such a way that the odd-paired lines share a singular line's memory,
        making the first line 0x00->0x13, the second line 0x40->0x53, the third line 0x14->0x27. and the
        fourth line from 0x54->0x67.

        Arguments:
            :index: Integer - 0-based index that you want to get the memory-address for.
        """

        # This is a fun bit-twiddling trick.  `n // m` can be rewritten as `n >> p` where `m = 2^p`.
        if index >> 4:
            offset = 0x40
        else:
            offset = 0x00
        # Another fun bit-twiddling trick. `n % m` can be rewritten as `(n & 2^p) - 1` where `m = 2^p`.
        index &= 0x0F

        # The address is simply the offset + index after moduloing 16 (Note: We can use the OR operator to perform
        # addition here since we're gauranteed that our first and second nibbles will be completely separate).
        return index | offset
