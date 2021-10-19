from unittest import mock

import pytest


@pytest.fixture(autouse=True)
def mock_smbus():
    with mock.patch("smbus.SMBus") as smbus_mock:
        yield smbus_mock
