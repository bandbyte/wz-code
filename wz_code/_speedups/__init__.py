"""Optional Cython extensions for performance optimization.

This module provides optional Cython-based implementations of performance-critical
operations. If Cython extensions are not available, the package falls back to
pure Python implementations.
"""

try:
    # Try to import Cython extensions
    from wz_code._speedups import search as _search_ext  # type: ignore
    from wz_code._speedups import trie as _trie_ext  # type: ignore
    from wz_code._speedups import similarity as _similarity_ext  # type: ignore

    CYTHON_AVAILABLE = True
except ImportError:
    CYTHON_AVAILABLE = False

__all__ = ["CYTHON_AVAILABLE"]
