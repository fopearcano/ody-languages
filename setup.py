"""Compatibility shim: everything lives in pyproject.toml.

Kept so that ``pip install -e .`` also works on older pip/setuptools
without PEP 660 editable-install support.
"""

from setuptools import setup

setup()
