"""Package-wide tests."""

import importlib

import pytest


@pytest.mark.parametrize(
    "item_name",
    (
        "LCD",
        "PCF8574I2CBackpackInterface",
    ),
)
def test_thing_should_be_importable(item_name):
    module = importlib.import_module("simple_hd44780")

    assert hasattr(module, item_name)
