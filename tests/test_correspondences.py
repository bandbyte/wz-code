"""Tests for correspondence functionality."""

import pytest

from wz_code import WZ, Correspondence, WZCodeNotFoundError, WZVersionError


class TestCorrespondenceData:
    """Tests for correspondence data integrity."""

    def test_correspondence_data_loads(self) -> None:
        """Test that correspondence data loads successfully."""
        wz2025 = WZ(version="2025")
        wz2008 = WZ(version="2008")

        # Should not raise errors
        assert wz2025._correspondences_forward is not None
        assert wz2025._correspondences_reverse is not None
        assert wz2008._correspondences_forward is not None
        assert wz2008._correspondences_reverse is not None

    def test_correspondence_data_structure(self) -> None:
        """Test correspondence data has expected structure."""
        wz = WZ(version="2025")

        # Forward map should have WZ 2025 codes
        assert len(wz._correspondences_forward) > 0

        # Each forward entry should have tuples with 3 elements
        for code, correspondences in wz._correspondences_forward.items():
            assert isinstance(code, str)
            assert isinstance(correspondences, list)
            for corr in correspondences:
                assert isinstance(corr, tuple)
                assert len(corr) == 3  # (wz2008_code, is_partial, title)
                assert isinstance(corr[0], str)
                assert isinstance(corr[1], bool)
                assert isinstance(corr[2], str)


class TestCorrespondenceAPI:
    """Tests for correspondence API methods."""

    @pytest.fixture
    def wz2025(self) -> WZ:
        """Fixture for WZ 2025 instance."""
        return WZ(version="2025")

    @pytest.fixture
    def wz2008(self) -> WZ:
        """Fixture for WZ 2008 instance."""
        return WZ(version="2008")

    def test_get_correspondences_wz2025(self, wz2025: WZ) -> None:
        """Test getting correspondences for a WZ 2025 code."""
        correspondences = wz2025.get_correspondences("01.13.1")

        assert isinstance(correspondences, list)
        assert len(correspondences) > 0
        assert all(isinstance(c, Correspondence) for c in correspondences)

        # Should have at least one full match and partial matches
        full = [c for c in correspondences if not c.is_partial]
        partial = [c for c in correspondences if c.is_partial]
        assert len(full) >= 1
        assert len(partial) >= 1

        # All correspondences should be WZ 2008
        assert all(c.version == "2008" for c in correspondences)

    def test_get_correspondences_wz2008(self, wz2008: WZ) -> None:
        """Test getting correspondences for a WZ 2008 code."""
        correspondences = wz2008.get_correspondences("01.19.9")

        assert isinstance(correspondences, list)
        assert len(correspondences) > 0
        assert all(isinstance(c, Correspondence) for c in correspondences)

        # All correspondences should be WZ 2025
        assert all(c.version == "2025" for c in correspondences)

    def test_get_correspondences_nonexistent_code(self, wz2025: WZ) -> None:
        """Test getting correspondences for a non-existent code."""
        correspondences = wz2025.get_correspondences("INVALID")
        assert correspondences == []

    def test_get_correspondences_code_without_correspondences(self, wz2025: WZ) -> None:
        """Test getting correspondences for a code without correspondences."""
        # High-level codes typically don't have correspondences
        correspondences = wz2025.get_correspondences("A")
        assert correspondences == []

    def test_wzcode_correspondences_property(self, wz2025: WZ) -> None:
        """Test the correspondences property on WZCode instances."""
        code = wz2025.get("01.13.1")
        correspondences = code.correspondences

        assert isinstance(correspondences, list)
        assert len(correspondences) > 0
        assert all(isinstance(c, Correspondence) for c in correspondences)

    def test_find_equivalent_2025_to_2008(self, wz2025: WZ) -> None:
        """Test finding equivalent codes from WZ 2025 to WZ 2008."""
        equivalents = wz2025.find_equivalent("01.13.1", "2008")

        assert isinstance(equivalents, list)
        assert len(equivalents) > 0
        assert all(c.version == "2008" for c in equivalents)

    def test_find_equivalent_2008_to_2025(self, wz2008: WZ) -> None:
        """Test finding equivalent codes from WZ 2008 to WZ 2025."""
        equivalents = wz2008.find_equivalent("01.19.9", "2025")

        assert isinstance(equivalents, list)
        assert len(equivalents) > 0
        assert all(c.version == "2025" for c in equivalents)

    def test_find_equivalent_same_version(self, wz2025: WZ) -> None:
        """Test that finding equivalents in same version returns empty list."""
        equivalents = wz2025.find_equivalent("01.13.1", "2025")
        assert equivalents == []

    def test_find_equivalent_invalid_version(self, wz2025: WZ) -> None:
        """Test that finding equivalents with invalid version raises error."""
        with pytest.raises(WZVersionError):
            wz2025.find_equivalent("01.13.1", "2020")


class TestBidirectionalMapping:
    """Tests for bidirectional correspondence mappings."""

    def test_forward_and_reverse_consistency(self) -> None:
        """Test that forward and reverse mappings are consistent."""
        wz2025 = WZ(version="2025")
        wz2008 = WZ(version="2008")

        # Get forward mapping for a WZ 2025 code
        wz2025_code = "01.13.1"
        forward_correspondences = wz2025.get_correspondences(wz2025_code)

        # For each WZ 2008 code in forward mapping, check reverse
        for corr in forward_correspondences:
            wz2008_code = corr.code
            reverse_correspondences = wz2008.get_correspondences(wz2008_code)

            # The original WZ 2025 code should be in the reverse correspondences
            reverse_codes = [c.code for c in reverse_correspondences]
            assert wz2025_code in reverse_codes

    def test_specific_bidirectional_example(self) -> None:
        """Test a specific bidirectional mapping example."""
        wz2025 = WZ(version="2025")
        wz2008 = WZ(version="2008")

        # WZ 2025: 01.13.1 should map to WZ 2008: 01.13.1
        forward = wz2025.get_correspondences("01.13.1")
        forward_codes = [c.code for c in forward]
        assert "01.13.1" in forward_codes

        # WZ 2008: 01.13.1 should map back to WZ 2025: 01.13.1
        reverse = wz2008.get_correspondences("01.13.1")
        reverse_codes = [c.code for c in reverse]
        assert "01.13.1" in reverse_codes


class TestPartialMatches:
    """Tests for partial vs. full correspondence matches."""

    def test_partial_flag_present(self) -> None:
        """Test that partial flag is properly set."""
        wz = WZ(version="2025")
        correspondences = wz.get_correspondences("01.13.1")

        # Should have both full and partial matches
        assert any(not c.is_partial for c in correspondences)
        assert any(c.is_partial for c in correspondences)

    def test_full_match_example(self) -> None:
        """Test that full matches have is_partial=False."""
        wz = WZ(version="2025")
        correspondences = wz.get_correspondences("01.11.0")

        # 01.11.0 should have a full match to itself
        full_matches = [c for c in correspondences if not c.is_partial]
        assert len(full_matches) >= 1
        assert any(c.code == "01.11.0" for c in full_matches)

    def test_correspondence_string_representation(self) -> None:
        """Test the string representation of Correspondence objects."""
        wz = WZ(version="2025")
        correspondences = wz.get_correspondences("01.13.1")

        for corr in correspondences:
            str_repr = str(corr)
            assert corr.code in str_repr
            assert corr.title in str_repr
            if corr.is_partial:
                assert "partial" in str_repr
            else:
                assert "full" in str_repr


class TestCorrespondencePerformance:
    """Performance tests for correspondence operations."""

    def test_correspondence_lookup_performance(self) -> None:
        """Test that correspondence lookups are fast."""
        import time

        wz = WZ(version="2025")

        # Warm up
        wz.get_correspondences("01.13.1")

        # Time 100 lookups
        start = time.time()
        for _ in range(100):
            wz.get_correspondences("01.13.1")
        elapsed = time.time() - start

        # Should be very fast (< 10ms total for 100 lookups)
        assert elapsed < 0.01, f"100 lookups took {elapsed*1000:.2f}ms, expected < 10ms"

    def test_import_time_with_correspondences(self) -> None:
        """Test that import time is still fast with correspondences loaded."""
        import subprocess
        import time

        # Measure import time
        start = time.time()
        result = subprocess.run(
            ["python", "-c", "import wz_code"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        elapsed = time.time() - start

        assert result.returncode == 0
        # Import should still be fast (< 100ms)
        assert elapsed < 0.1, f"Import took {elapsed*1000:.2f}ms, expected < 100ms"


class TestCorrespondenceModel:
    """Tests for the Correspondence dataclass."""

    def test_correspondence_creation(self) -> None:
        """Test creating a Correspondence instance."""
        corr = Correspondence(
            code="01.11.0",
            title="Test Title",
            is_partial=False,
            version="2008",
        )

        assert corr.code == "01.11.0"
        assert corr.title == "Test Title"
        assert corr.is_partial is False
        assert corr.version == "2008"

    def test_correspondence_frozen(self) -> None:
        """Test that Correspondence instances are immutable."""
        corr = Correspondence(
            code="01.11.0",
            title="Test Title",
            is_partial=False,
            version="2008",
        )

        with pytest.raises(AttributeError):
            corr.code = "01.12.0"  # type: ignore

    def test_correspondence_repr(self) -> None:
        """Test the repr of Correspondence."""
        corr = Correspondence(
            code="01.11.0",
            title="Test Title",
            is_partial=True,
            version="2008",
        )

        repr_str = repr(corr)
        assert "Correspondence" in repr_str
        assert "01.11.0" in repr_str
        assert "is_partial=True" in repr_str
        assert "2008" in repr_str
