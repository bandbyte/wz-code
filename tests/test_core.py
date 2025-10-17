"""Tests for core functionality."""

import pytest

from wz_code import WZ, WZCode, WZCodeNotFoundError, WZVersionError
from wz_code.models import WZVersion


class TestWZInitialization:
    """Tests for WZ initialization."""

    def test_init_with_string_2025(self) -> None:
        """Test initialization with string version '2025'."""
        wz = WZ(version="2025")
        assert wz._version == "2025"
        assert len(wz) == 2030

    def test_init_with_string_2008(self) -> None:
        """Test initialization with string version '2008'."""
        wz = WZ(version="2008")
        assert wz._version == "2008"
        assert len(wz) == 1835

    def test_init_with_enum(self) -> None:
        """Test initialization with WZVersion enum."""
        wz = WZ(version=WZVersion.WZ_2025)
        assert wz._version == "2025"

    def test_init_invalid_version(self) -> None:
        """Test initialization with invalid version."""
        with pytest.raises(WZVersionError) as exc_info:
            WZ(version="2020")
        assert "2020" in str(exc_info.value)
        assert "2008" in str(exc_info.value)
        assert "2025" in str(exc_info.value)


class TestWZCodeLookup:
    """Tests for code lookup functionality."""

    @pytest.fixture
    def wz2025(self) -> WZ:
        """Fixture for WZ 2025 instance."""
        return WZ(version="2025")

    @pytest.fixture
    def wz2008(self) -> WZ:
        """Fixture for WZ 2008 instance."""
        return WZ(version="2008")

    def test_get_top_level_code(self, wz2025: WZ) -> None:
        """Test getting a top-level code."""
        agriculture = wz2025.get("A")
        assert agriculture.code == "A"
        assert agriculture.title == "Land- und Forstwirtschaft, Fischerei"
        assert agriculture.level == 1
        assert agriculture.version == "2025"

    def test_get_nested_code(self, wz2025: WZ) -> None:
        """Test getting a nested code."""
        code = wz2025.get("01.11")
        assert code.code == "01.11"
        assert code.level == 4

    def test_get_nonexistent_code(self, wz2025: WZ) -> None:
        """Test getting a non-existent code."""
        with pytest.raises(WZCodeNotFoundError) as exc_info:
            wz2025.get("INVALID")
        assert "INVALID" in str(exc_info.value)
        assert "2025" in str(exc_info.value)

    def test_exists(self, wz2025: WZ) -> None:
        """Test code existence check."""
        assert wz2025.exists("A") is True
        assert wz2025.exists("INVALID") is False

    def test_get_all_codes(self, wz2025: WZ) -> None:
        """Test getting all codes."""
        codes = wz2025.get_all_codes()
        assert len(codes) == 2030
        assert "A" in codes
        assert sorted(codes) == codes  # Should be sorted

    def test_get_top_level_codes_2025(self, wz2025: WZ) -> None:
        """Test getting top-level codes for WZ 2025."""
        top_level = wz2025.get_top_level_codes()
        assert len(top_level) == 22  # WZ 2025 has 22 top-level codes
        assert all(isinstance(code, WZCode) for code in top_level)
        assert all(code.level == 1 for code in top_level)

    def test_get_top_level_codes_2008(self, wz2008: WZ) -> None:
        """Test getting top-level codes for WZ 2008 (hierarchical structure)."""
        top_level = wz2008.get_top_level_codes()
        assert len(top_level) == 21  # WZ 2008 has 21 top-level codes
        assert all(isinstance(code, WZCode) for code in top_level)
        assert all(code.level == 1 for code in top_level)


class TestWZCodeHierarchy:
    """Tests for hierarchical navigation."""

    @pytest.fixture
    def wz2025(self) -> WZ:
        """Fixture for WZ 2025 instance."""
        return WZ(version="2025")

    @pytest.fixture
    def wz2008(self) -> WZ:
        """Fixture for WZ 2008 instance."""
        return WZ(version="2008")

    def test_parent(self, wz2025: WZ) -> None:
        """Test parent relationship."""
        code = wz2025.get("01.11")
        parent = code.parent
        assert parent is not None
        assert parent.code == "01.1"

    def test_parent_of_top_level(self, wz2025: WZ) -> None:
        """Test that top-level codes have no parent."""
        agriculture = wz2025.get("A")
        assert agriculture.parent is None

    def test_children(self, wz2025: WZ) -> None:
        """Test children relationship."""
        agriculture = wz2025.get("A")
        children = agriculture.children
        assert len(children) == 3
        assert all(isinstance(child, WZCode) for child in children)
        child_codes = [child.code for child in children]
        assert "01" in child_codes
        assert "02" in child_codes
        assert "03" in child_codes

    def test_ancestors(self, wz2025: WZ) -> None:
        """Test ancestors retrieval."""
        code = wz2025.get("01.11")
        ancestors = code.ancestors
        ancestor_codes = [a.code for a in ancestors]
        assert "01.1" in ancestor_codes
        assert "01" in ancestor_codes
        assert "A" in ancestor_codes

    def test_descendants(self, wz2025: WZ) -> None:
        """Test descendants retrieval."""
        agriculture = wz2025.get("A")
        descendants = agriculture.descendants
        assert len(descendants) > 100  # Agriculture has many descendants
        assert all(isinstance(d, WZCode) for d in descendants)

    def test_wz2008_hierarchy(self, wz2008: WZ) -> None:
        """Test that WZ 2008 now has proper hierarchical structure."""
        # Test top-level code
        agriculture = wz2008.get("A")
        assert agriculture.level == 1
        assert agriculture.parent is None
        assert len(agriculture.children) > 0

        # Test nested code
        code = wz2008.get("01.11.0")
        assert code.level == 5
        assert code.parent is not None
        assert code.parent.code == "01.11"

        # Test ancestors
        ancestors = code.ancestors
        assert len(ancestors) > 0
        ancestor_codes = [a.code for a in ancestors]
        assert "01.11" in ancestor_codes
        assert "01.1" in ancestor_codes
        assert "01" in ancestor_codes
        assert "A" in ancestor_codes


class TestWZCodeMethods:
    """Tests for WZCode methods."""

    @pytest.fixture
    def wz2025(self) -> WZ:
        """Fixture for WZ 2025 instance."""
        return WZ(version="2025")

    def test_str(self, wz2025: WZ) -> None:
        """Test string representation."""
        agriculture = wz2025.get("A")
        assert str(agriculture) == "A: Land- und Forstwirtschaft, Fischerei"

    def test_repr(self, wz2025: WZ) -> None:
        """Test detailed representation."""
        agriculture = wz2025.get("A")
        repr_str = repr(agriculture)
        assert "WZCode" in repr_str
        assert "A" in repr_str
        assert "2025" in repr_str

    def test_equality(self, wz2025: WZ) -> None:
        """Test equality comparison."""
        code1 = wz2025.get("A")
        code2 = wz2025.get("A")
        assert code1 == code2

    def test_inequality_different_code(self, wz2025: WZ) -> None:
        """Test inequality with different codes."""
        code1 = wz2025.get("A")
        code2 = wz2025.get("B")
        assert code1 != code2

    def test_hash(self, wz2025: WZ) -> None:
        """Test that codes are hashable."""
        agriculture = wz2025.get("A")
        code_set = {agriculture}
        assert agriculture in code_set


class TestWZSearch:
    """Tests for search functionality."""

    @pytest.fixture
    def wz2025(self) -> WZ:
        """Fixture for WZ 2025 instance."""
        return WZ(version="2025")

    @pytest.fixture
    def wz2008(self) -> WZ:
        """Fixture for WZ 2008 instance."""
        return WZ(version="2008")

    def test_search_in_titles(self, wz2025: WZ) -> None:
        """Test search in titles."""
        results = wz2025.search_in_titles("Landwirtschaft")
        assert len(results) > 0
        assert all(isinstance(r, WZCode) for r in results)
        assert any("Landwirtschaft" in r.title for r in results)

    def test_search_in_titles_case_insensitive(self, wz2025: WZ) -> None:
        """Test case-insensitive search."""
        results = wz2025.search_in_titles("landwirtschaft")
        assert len(results) > 0

    def test_search_in_titles_case_sensitive(self, wz2025: WZ) -> None:
        """Test case-sensitive search."""
        # Search for uppercase which should give different results than lowercase
        results_upper = wz2025.search_in_titles("LAND", case_sensitive=True)
        results_lower = wz2025.search_in_titles("land", case_sensitive=True)
        assert results_upper != results_lower  # Different results due to case sensitivity


class TestPerformance:
    """Tests for performance requirements."""

    def test_import_time(self) -> None:
        """Test that import time is reasonable."""
        import time

        start = time.perf_counter()
        from wz_code import WZ  # noqa: F401

        end = time.perf_counter()
        import_time = (end - start) * 1000  # Convert to milliseconds
        assert import_time < 50, f"Import took {import_time:.2f}ms (requirement: <50ms)"

    def test_lookup_time(self) -> None:
        """Test that lookups are fast."""
        import time

        wz = WZ(version="2025")

        start = time.perf_counter()
        wz.get("A")
        end = time.perf_counter()

        lookup_time = (end - start) * 1000  # Convert to milliseconds
        assert lookup_time < 1, f"Lookup took {lookup_time:.2f}ms (requirement: <1ms)"

    def test_multiple_lookups(self) -> None:
        """Test performance with multiple lookups."""
        import time

        wz = WZ(version="2025")
        codes = ["A", "01", "01.1", "01.11", "B", "C"]

        start = time.perf_counter()
        for code in codes * 100:  # 600 lookups total
            wz.get(code)
        end = time.perf_counter()

        total_time = (end - start) * 1000
        avg_time = total_time / 600
        assert avg_time < 1, f"Average lookup took {avg_time:.4f}ms (requirement: <1ms)"
