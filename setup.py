# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------
from setuptools import setup, find_packages

setup(
    name="jito_py",
    version="0.1.2",
    description="A Python library for interacting with the Jito JSON-RPC",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/MatrixYe/jito-py",
    author="Matrix.Ye",
    author_email="initsysctrl@outlook.com",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "requests"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
