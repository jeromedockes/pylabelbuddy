#!/usr/bin/env python

from pathlib import Path

from setuptools import setup, find_packages

version = (
    Path(__file__)
    .parent.joinpath("src", "labelbuddy", "_data", "VERSION.txt")
    .read_text(encoding="utf-8")
    .strip()
)

description = "A small application for annotating text"

setup(
    name="labelbuddy",
    description=description,
    version=version,
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={"labelbuddy._data": ["*"]},
    install_requires=[],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "labelbuddy = labelbuddy._label_buddy:start_label_buddy"
        ]
    },
    maintainer="Jerome Dockes",
    maintainer_email="jerome@dockes.org",
    license="BSD 3-Clause License",
    classifiers=["Programming Language :: Python :: 3"],
    url="https://github.com/jeromedockes/labelbuddy"
)
