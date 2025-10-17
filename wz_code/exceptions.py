"""Custom exceptions for the wz-code package."""


class WZCodeError(Exception):
    """Base exception for all wz-code package errors."""

    pass


class WZCodeNotFoundError(WZCodeError, KeyError):
    """Raised when a WZ code is not found in the classification.

    Args:
        code: The WZ code that was not found.
        version: The WZ version being used (2008 or 2025).

    Example:
        >>> wz = WZ(version="2025")
        >>> wz.get("INVALID")  # doctest: +SKIP
        WZCodeNotFoundError: Code 'INVALID' not found in WZ 2025
    """

    def __init__(self, code: str, version: str) -> None:
        self.code = code
        self.version = version
        super().__init__(f"Code '{code}' not found in WZ {version}")


class WZVersionError(WZCodeError, ValueError):
    """Raised when an invalid WZ version is specified.

    Args:
        version: The invalid version that was provided.
        valid_versions: List of valid version strings.

    Example:
        >>> WZ(version="2020")  # doctest: +SKIP
        WZVersionError: Invalid WZ version '2020'. Valid versions: ['2008', '2025']
    """

    def __init__(self, version: str, valid_versions: list[str]) -> None:
        self.version = version
        self.valid_versions = valid_versions
        valid_str = ", ".join(f"'{v}'" for v in valid_versions)
        super().__init__(f"Invalid WZ version '{version}'. Valid versions: [{valid_str}]")


class WZDataError(WZCodeError):
    """Raised when there is an error with the WZ data structure or integrity.

    Args:
        message: Description of the data error.

    Example:
        >>> raise WZDataError("Missing parent reference for code '01.1'")
        WZDataError: Missing parent reference for code '01.1'
    """

    pass
