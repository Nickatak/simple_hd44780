from setuptools import find_packages, setup

VERSION = "0.0.1"
DESCRIPTION = "Simple library for HD44780 compliant LCD's."
with open("README.md") as fo:
    LONG_DESCRIPTION = fo.read()

setup(
    name="simple_hd44780",
    version=VERSION,
    author="Nickatak",
    author_email="nickle87@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("tests",)),
    license="LICENSE.txt",
)
