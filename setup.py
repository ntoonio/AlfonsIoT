import setuptools
import os
import re

PATH = os.path.dirname(os.path.abspath(__file__)) + "/"

installRequires = []

with open(PATH + "requirements.txt", "r") as f:
	for l in f.readlines():
		l = re.sub("(#|-e).*$", "", l) # Remove comments and lines that start with -e
		l = l.rstrip().lstrip()

		if not l == "": # Empty lines (and commented lines which now are empty) will be removed
			installRequires.append(l)

with open(PATH + "README.md", "r") as fh:
	long_description = fh.read()

setuptools.setup(
	name="alfonsiot",
	version="0.0.7",
	author="Anton Lindroth",
	author_email="ntoonio@gmail.com",
	description="A package for IoTs to interact with Alfons",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/ntoonio/AlfonsIoT",
	packages=setuptools.find_packages(),
	install_requires=installRequires
)
