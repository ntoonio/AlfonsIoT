import setuptools
import os
import re

PATH = os.path.dirname(os.path.abspath(__file__)) + "/"

with open(PATH + "README.md", "r") as fh:
	long_description = fh.read()

setuptools.setup(
	name="alfonsiot",
	version="0.0.10",
	author="Anton Lindroth",
	author_email="ntoonio@gmail.com",
	description="A package for IoTs to interact with Alfons",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/ntoonio/AlfonsIoT",
	packages=setuptools.find_packages(),
	install_requires=[
		"paho-mqtt==1.5.0",
		"requests==2.25.1"
	]
)
