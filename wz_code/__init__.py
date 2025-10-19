"""
WZ-Code: High-performance German economic classification (WZ) library.

This package provides seamless access to both WZ 2008 and WZ 2025 classifications
with embedded data for zero-configuration usage.

Example usage:
    >>> from wz_code import WZ
    >>> wz = WZ(version="2025")
    >>> agriculture = wz.get("A")
    >>> print(agriculture.title)
    LAND- UND FORSTWIRTSCHAFT, FISCHEREI
"""

from wz_code.core import WZ, WZCode
from wz_code.exceptions import (
    WZCodeError,
    WZCodeNotFoundError,
    WZVersionError,
    WZDataError,
)
from wz_code.models import Correspondence, WZVersion

__version__ = "0.1.0"
__all__ = [
    "WZ",
    "WZCode",
    "WZVersion",
    "Correspondence",
    "WZCodeError",
    "WZCodeNotFoundError",
    "WZVersionError",
    "WZDataError",
]
