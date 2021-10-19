from simple_hd44780.interfaces.base import BaseInterface


class RPiGPIO4BitInterface(BaseInterface):
    """RPi.GPIO interface to drive the HD44780 LCD in 4-bit operation mode."""

    def __init__(
        self,
        rs_bit=0,
        rw_bit=1,
        e_bit=2,
        a_bit=3,
        data_bits=[4, 5, 6, 7],
    ):
        """Creates a new RPiGPIOInterface object.

        The integer for each bit is the Pin Number.
        """

        pass
