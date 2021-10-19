class BaseException(Exception):
    """Base exception class for which all our exceptions will innherit from."""


class InvalidDisplayConfError(BaseException):
    """Raised if an invalid display configuration was attempted to be set.

    The only invalid configuration is if you try to set the display to 2 lines
    AND 50 dots per char.
    """

    def __init__(self):
        msg = (
            "Invalid configuration: the HD44780 does NOT support displaying "
            "2 lines with a character resolution of 5x10."
        )

        super().__init__(msg)
