#!usr/bin/env python3
# -*- coding: utf-8 -*-
#
# setup.py
#
##############################################################################
# REQUIRED MODULES
##############################################################################
from setuptools import setup


##############################################################################
# MAIN
##############################################################################
if __name__ == '__main__':

    with open("README.md", "r") as fh:
        long_description = fh.read()

    setup(
        name="up_template",
        version="3.0.0",
        license="CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        packages=['up_template'],
        install_requires=[
            "netlolca @ git+https://github.com/NETL-RIC/netlolca#egg=netlolca",
            "pandas",
            "sympy",
            "tabulate",
            "jupyterlab",
        ],
        author="Tyler W. Davis, Priyadarshini, Joseph Chou, and Matt Jamieson",
        author_email="matthew.jamieson@netl.doe.gov",
        description="The NETL Unit Process Template and Report Generator",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/NETL-RIC/up_template",
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.12',
            # Can't confirm it works with Python 3.13 or later!
        ],
        python_requires='>=3.9',
    )
