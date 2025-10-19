"""Core classes for the wz-code package."""

from functools import lru_cache
from typing import Any

from wz_code.exceptions import WZCodeNotFoundError, WZVersionError
from wz_code.models import Correspondence, WZVersion


class WZCode:
    """Represents a single WZ classification code.

    This class provides access to a WZ code's properties and hierarchical relationships.
    Uses __slots__ for memory efficiency.

    Attributes:
        code: The WZ code (e.g., "A", "01", "01.1", "01.11").
        title: German description of the classification.
        level: Hierarchical level (1-5).
        version: WZ version ("2008" or "2025").

    Example:
        >>> wz = WZ(version="2025")
        >>> agriculture = wz.get("A")
        >>> agriculture.code
        'A'
        >>> agriculture.title
        'LAND- UND FORSTWIRTSCHAFT, FISCHEREI'
        >>> agriculture.level
        1
    """

    __slots__ = ("_code", "_title", "_level", "_version", "_parent_code", "_children_codes", "_wz")

    def __init__(
        self,
        code: str,
        title: str,
        level: int,
        version: str,
        parent_code: str | None,
        children_codes: list[str] | None,
        wz_instance: "WZ",
    ) -> None:
        """Initialize a WZCode instance.

        Args:
            code: The WZ code.
            title: German description.
            level: Hierarchical level.
            version: WZ version.
            parent_code: Parent code reference (if any).
            children_codes: List of children codes (if any).
            wz_instance: Reference to the WZ instance for lazy loading.
        """
        self._code = code
        self._title = title
        self._level = level
        self._version = version
        self._parent_code = parent_code
        self._children_codes = children_codes or []
        self._wz = wz_instance

    @property
    def code(self) -> str:
        """Return the WZ code."""
        return self._code

    @property
    def title(self) -> str:
        """Return the German title/description."""
        return self._title

    @property
    def level(self) -> int:
        """Return the hierarchical level (1-5)."""
        return self._level

    @property
    def version(self) -> str:
        """Return the WZ version (\"2008\" or \"2025\")."""
        return self._version

    @property
    def parent(self) -> "WZCode | None":
        """Return the parent WZCode, or None if this is a top-level code.

        Example:
            >>> wz = WZ(version="2025")
            >>> code = wz.get("01.1")
            >>> code.parent.code
            '01'
        """
        if self._parent_code:
            return self._wz.get(self._parent_code)
        return None

    @property
    def children(self) -> list["WZCode"]:
        """Return a list of child WZCode objects.

        Example:
            >>> wz = WZ(version="2025")
            >>> agriculture = wz.get("A")
            >>> [child.code for child in agriculture.children]
            ['01', '02', '03']
        """
        return [self._wz.get(code) for code in self._children_codes]

    @property
    def ancestors(self) -> list["WZCode"]:
        """Return a list of all ancestor codes from parent to root.

        Example:
            >>> wz = WZ(version="2025")
            >>> code = wz.get("01.11")
            >>> [a.code for a in code.ancestors]
            ['01.1', '01', 'A']
        """
        ancestors: list[WZCode] = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    @property
    def descendants(self) -> list["WZCode"]:
        """Return a list of all descendant codes (depth-first traversal).

        Example:
            >>> wz = WZ(version="2025")
            >>> agriculture = wz.get("A")
            >>> len(agriculture.descendants) > 100
            True
        """
        descendants: list[WZCode] = []

        def collect_descendants(code: WZCode) -> None:
            for child in code.children:
                descendants.append(child)
                collect_descendants(child)

        collect_descendants(self)
        return descendants

    @property
    def correspondences(self) -> list[Correspondence]:
        """Return correspondences to the other WZ version.

        For WZ 2025 codes, returns corresponding WZ 2008 codes.
        For WZ 2008 codes, returns corresponding WZ 2025 codes.

        Example:
            >>> wz = WZ(version="2025")
            >>> code = wz.get("01.13.1")
            >>> correspondences = code.correspondences
            >>> len(correspondences) > 0
            True
        """
        return self._wz.get_correspondences(self._code)

    def __str__(self) -> str:
        """Return a string representation of the code."""
        return f"{self._code}: {self._title}"

    def __repr__(self) -> str:
        """Return a detailed string representation."""
        return f"WZCode(code={self._code!r}, level={self._level}, version={self._version!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality based on code and version."""
        if not isinstance(other, WZCode):
            return False
        return self._code == other._code and self._version == other._version

    def __hash__(self) -> int:
        """Return hash based on code and version."""
        return hash((self._code, self._version))


class WZ:
    """Main interface for accessing WZ classification data.

    This class provides methods for code lookup, hierarchical navigation,
    and search operations. It lazy-loads data and caches frequently accessed codes.

    Args:
        version: WZ version to use ("2008" or "2025").

    Example:
        >>> wz = WZ(version="2025")
        >>> agriculture = wz.get("A")
        >>> print(agriculture.title)
        LAND- UND FORSTWIRTSCHAFT, FISCHEREI
    """

    def __init__(self, version: str | WZVersion) -> None:
        """Initialize the WZ interface.

        Args:
            version: WZ version ("2008" or "2025").

        Raises:
            WZVersionError: If the version is not valid.
        """
        # Normalize version
        if isinstance(version, WZVersion):
            self._version = version.value
        else:
            try:
                self._version = WZVersion.from_string(version).value
            except ValueError as e:
                valid_versions = [v.value for v in WZVersion]
                raise WZVersionError(version, valid_versions) from e

        # Load data
        self._data = self._load_data()

        # Load correspondences
        self._correspondences_forward, self._correspondences_reverse = self._load_correspondences()

        # Cache for WZCode instances
        self._code_cache: dict[str, WZCode] = {}

    def _load_data(self) -> dict[str, dict[str, Any]]:
        """Load the appropriate data module based on version.

        Returns:
            Dictionary mapping code -> data entry.
        """
        if self._version == "2025":
            from wz_code.data.wz2025 import WZ_2025_DATA

            return WZ_2025_DATA
        elif self._version == "2008":
            from wz_code.data.wz2008 import WZ_2008_DATA

            return WZ_2008_DATA
        else:
            # This should never happen due to validation in __init__
            raise WZVersionError(self._version, [v.value for v in WZVersion])

    def _load_correspondences(
        self,
    ) -> tuple[dict[str, list[tuple[str, bool, str]]], dict[str, list[tuple[str, str]]]]:
        """Load correspondence mappings between WZ versions.

        Returns:
            Tuple of (forward_map, reverse_map) where:
            - forward_map: WZ 2025 -> WZ 2008 correspondences (code, is_partial, title)
            - reverse_map: WZ 2008 -> WZ 2025 correspondences (code, title)
        """
        try:
            from wz_code.data.correspondences import (
                CORRESPONDENCES_2025_TO_2008,
                CORRESPONDENCES_2008_TO_2025,
            )

            return CORRESPONDENCES_2025_TO_2008, CORRESPONDENCES_2008_TO_2025
        except ImportError:
            # Correspondences not generated yet
            return {}, {}

    @lru_cache(maxsize=512)
    def get(self, code: str) -> WZCode:
        """Get a WZCode by its code string.

        Args:
            code: The WZ code to retrieve (e.g., "A", "01", "01.1").

        Returns:
            WZCode instance for the requested code.

        Raises:
            WZCodeNotFoundError: If the code is not found.

        Example:
            >>> wz = WZ(version="2025")
            >>> agriculture = wz.get("A")
            >>> agriculture.title
            'LAND- UND FORSTWIRTSCHAFT, FISCHEREI'
        """
        code = code.strip()

        # Check cache first
        if code in self._code_cache:
            return self._code_cache[code]

        # Look up in data
        if code not in self._data:
            raise WZCodeNotFoundError(code, self._version)

        entry = self._data[code]

        # Create WZCode instance
        wz_code = WZCode(
            code=code,
            title=entry["t"],
            level=entry["l"],
            version=self._version,
            parent_code=entry["p"],
            children_codes=entry["c"],
            wz_instance=self,
        )

        # Cache it
        self._code_cache[code] = wz_code

        return wz_code

    def exists(self, code: str) -> bool:
        """Check if a code exists in the classification.

        Args:
            code: The WZ code to check.

        Returns:
            True if the code exists, False otherwise.

        Example:
            >>> wz = WZ(version="2025")
            >>> wz.exists("A")
            True
            >>> wz.exists("INVALID")
            False
        """
        return code.strip() in self._data

    def get_all_codes(self) -> list[str]:
        """Return a list of all codes in the classification.

        Returns:
            Sorted list of all WZ codes.

        Example:
            >>> wz = WZ(version="2025")
            >>> len(wz.get_all_codes())
            2030
        """
        return sorted(self._data.keys())

    def get_top_level_codes(self) -> list[WZCode]:
        """Return all top-level codes (level 1).

        Returns:
            List of WZCode instances at level 1.

        Example:
            >>> wz = WZ(version="2025")
            >>> top_level = wz.get_top_level_codes()
            >>> [code.code for code in top_level]
            ['A', 'B', 'C', ...]
        """
        # Both WZ 2008 and WZ 2025 have hierarchical structure - return level 1
        return [self.get(code) for code in self._data if self._data[code]["l"] == 1]

    def search_in_titles(self, query: str, case_sensitive: bool = False) -> list[WZCode]:
        """Search for codes by substring match in titles.

        Args:
            query: Search query string.
            case_sensitive: Whether to perform case-sensitive search.

        Returns:
            List of matching WZCode instances.

        Example:
            >>> wz = WZ(version="2025")
            >>> results = wz.search_in_titles("Landwirtschaft")
            >>> len(results) > 0
            True
        """
        query = query if case_sensitive else query.lower()
        results: list[WZCode] = []

        for code in self._data:
            title = self._data[code]["t"]
            title_cmp = title if case_sensitive else title.lower()

            if query in title_cmp:
                results.append(self.get(code))

        return results

    def get_correspondences(self, code: str) -> list[Correspondence]:
        """Get correspondence mappings for a code.

        Args:
            code: The WZ code to get correspondences for.

        Returns:
            List of Correspondence objects. Returns empty list if code not found
            or no correspondences exist.

        Example:
            >>> wz = WZ(version="2025")
            >>> correspondences = wz.get_correspondences("01.13.1")
            >>> len(correspondences) > 0
            True
        """
        # Validate that the code exists
        if not self.exists(code):
            return []

        correspondences: list[Correspondence] = []

        if self._version == "2025":
            # Forward mapping: WZ 2025 -> WZ 2008
            if code in self._correspondences_forward:
                for wz2008_code, is_partial, title in self._correspondences_forward[code]:
                    correspondences.append(
                        Correspondence(
                            code=wz2008_code,
                            title=title,
                            is_partial=is_partial,
                            version="2008",
                        )
                    )
        elif self._version == "2008":
            # Reverse mapping: WZ 2008 -> WZ 2025
            if code in self._correspondences_reverse:
                for wz2025_code, title in self._correspondences_reverse[code]:
                    correspondences.append(
                        Correspondence(
                            code=wz2025_code,
                            title=title,
                            is_partial=False,  # Reverse mappings don't track partial status
                            version="2025",
                        )
                    )

        return correspondences

    def find_equivalent(self, code: str, target_version: str | WZVersion) -> list[Correspondence]:
        """Find equivalent codes in a target WZ version.

        This is a convenience method that normalizes the target version and
        calls get_correspondences().

        Args:
            code: The WZ code to find equivalents for.
            target_version: Target WZ version ("2008" or "2025").

        Returns:
            List of Correspondence objects in the target version.

        Raises:
            WZVersionError: If target_version is invalid.

        Example:
            >>> wz = WZ(version="2025")
            >>> equivalents = wz.find_equivalent("01.13.1", "2008")
            >>> len(equivalents) > 0
            True
        """
        # Normalize target version
        if isinstance(target_version, WZVersion):
            target_ver = target_version.value
        else:
            try:
                target_ver = WZVersion.from_string(target_version).value
            except ValueError as e:
                valid_versions = [v.value for v in WZVersion]
                raise WZVersionError(target_version, valid_versions) from e

        # If target version matches current version, return empty list
        if target_ver == self._version:
            return []

        # Otherwise, get correspondences
        return self.get_correspondences(code)

    def __repr__(self) -> str:
        """Return a string representation of the WZ instance."""
        return f"WZ(version={self._version!r}, codes={len(self._data)})"

    def __len__(self) -> int:
        """Return the number of codes in the classification."""
        return len(self._data)
