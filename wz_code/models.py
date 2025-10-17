"""Data models and type definitions for the wz-code package."""

from enum import Enum
from typing import TypedDict


class WZVersion(str, Enum):
    """Enumeration of supported WZ classification versions.

    Attributes:
        WZ_2008: WZ 2008 classification (final version for compatibility).
        WZ_2025: WZ 2025 classification (latest official version).
    """

    WZ_2008 = "2008"
    WZ_2025 = "2025"

    @classmethod
    def from_string(cls, version: str) -> "WZVersion":
        """Convert a string to a WZVersion enum.

        Args:
            version: Version string ("2008" or "2025").

        Returns:
            Corresponding WZVersion enum value.

        Raises:
            ValueError: If the version string is not valid.

        Example:
            >>> WZVersion.from_string("2025")
            <WZVersion.WZ_2025: '2025'>
        """
        try:
            return cls(version)
        except ValueError:
            valid_versions = [v.value for v in cls]
            raise ValueError(
                f"Invalid WZ version '{version}'. Valid versions: {valid_versions}"
            ) from None

    def __str__(self) -> str:
        """Return the version string."""
        return self.value


class WZDataEntry(TypedDict):
    """Type definition for a WZ data entry (internal storage format).

    This is the optimized internal format used in the generated data modules.
    Uses short keys to minimize memory usage.

    Attributes:
        l: Level (1-5 for hierarchical codes, 0 for flat codes).
        t: Title (German description).
        p: Parent code reference (optional, only for hierarchical codes).
        c: List of children codes (optional, only for hierarchical codes).
    """

    l: int
    t: str
    p: str | None
    c: list[str] | None


class WZCodeData(TypedDict):
    """Type definition for WZ code data (public API format).

    This is the format returned by the public API methods.

    Attributes:
        code: The WZ code (e.g., "A", "01", "01.1", "01.11").
        title: German description of the classification.
        level: Hierarchical level (1-5).
        version: WZ version ("2008" or "2025").
    """

    code: str
    title: str
    level: int
    version: str
