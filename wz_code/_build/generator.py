"""Data generator for converting XML files to optimized Python modules.

This module reads the official WZ XML files and generates optimized Python data
modules that are embedded in the package for zero-configuration usage.

Usage:
    python -m wz_code._build.generator --wz2025 source/WZ_2025_DE_2025-08-19.xml --wz2008 source/WZ_2008_DE_2025-09-29.xml
"""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def read_wz_xml(xml_path: Path) -> dict[str, dict[str, Any]]:
    """Read WZ classification from XML file.

    Args:
        xml_path: Path to the WZ XML file.

    Returns:
        Dictionary mapping code -> data entry.
        Data entry contains: {l: level, t: title, p: parent, c: children}

    Example:
        >>> data = read_wz_xml(Path("source/WZ_2025_DE_2025-08-19.xml"))
        >>> data["A"]
        {'l': 1, 't': 'Land- und Forstwirtschaft, Fischerei', 'p': None, 'c': ['01', '02', '03']}
    """
    print(f"Reading WZ classification from {xml_path}...")

    # Parse XML
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Find SimpleCodeList element
    simple_code_list = None
    for child in root:
        tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag_name == 'SimpleCodeList':
            simple_code_list = child
            break

    if simple_code_list is None:
        raise ValueError(f"No SimpleCodeList found in {xml_path}")

    # All children of SimpleCodeList are Row elements
    rows = list(simple_code_list)

    data: dict[str, dict[str, Any]] = {}
    parent_stack: list[tuple[int, str]] = []  # Stack of (level, code)

    for row in rows:
        # Extract values from the row (each child is a Value element)
        code = None
        level = None
        title = None

        for val in row:
            col_ref = val.get('ColumnRef')
            # First child of Value is SimpleValue
            simple_val = list(val)[0] if len(val) > 0 else None

            if simple_val is not None and simple_val.text:
                if col_ref == 'ItemCode':
                    code = simple_val.text.strip()
                elif col_ref == 'ItemEbene':
                    level = int(simple_val.text.strip())
                elif col_ref == 'ItemOffiziellerTitel':
                    title = simple_val.text.strip()

        # Skip if essential data is missing
        if not code or level is None or not title:
            continue

        # Determine parent based on level hierarchy
        parent_code: str | None = None
        while parent_stack and parent_stack[-1][0] >= level:
            parent_stack.pop()

        if parent_stack:
            parent_code = parent_stack[-1][1]

        # Add entry to data
        data[code] = {
            "l": level,
            "t": title,
            "p": parent_code,
            "c": [],  # Will be populated later
        }

        # Update parent stack
        parent_stack.append((level, code))

    # Now populate children lists by iterating through all codes
    for code, entry in data.items():
        parent = entry["p"]
        if parent and parent in data:
            data[parent]["c"].append(code)

    print(f"  Read {len(data)} codes")

    # Print level distribution
    levels: dict[int, int] = {}
    for entry in data.values():
        level = entry["l"]
        levels[level] = levels.get(level, 0) + 1

    for level in sorted(levels.keys()):
        print(f"    Level {level}: {levels[level]} codes")

    return data


def read_correspondence_xml(xml_path: Path) -> tuple[dict[str, list[tuple[str, bool]]], dict[str, list[str]]]:
    """Read correspondence mappings from XML file.

    Args:
        xml_path: Path to the correspondence XML file.

    Returns:
        Tuple of (forward_map, reverse_map) where:
        - forward_map: WZ 2025 code -> list of (WZ 2008 code, is_partial)
        - reverse_map: WZ 2008 code -> list of WZ 2025 codes

    Example:
        >>> forward, reverse = read_correspondence_xml(Path("source/correspondences.xml"))
        >>> forward["01.13.1"]
        [("01.13.1", False), ("01.19.9", True), ("01.28.0", True)]
    """
    print(f"Reading correspondences from {xml_path}...")

    # Parse XML
    tree = ET.parse(xml_path)
    root = tree.getroot()

    forward_map: dict[str, list[tuple[str, bool]]] = {}
    reverse_map: dict[str, list[str]] = {}

    # Find all Item elements
    items = root.findall('.//Item')
    print(f"  Found {len(items)} items")

    for item in items:
        wz2025_code = item.get('id')
        if not wz2025_code:
            continue

        # Find all Generic properties (correspondences to WZ 2008)
        props = [p for p in item.findall('Property') if p.get('name') == 'Generic']

        if not props:
            continue

        correspondences: list[tuple[str, bool]] = []

        for prop in props:
            # Extract WZ 2008 code and description
            wz2008_code = None
            is_partial = False

            for prop_text in prop.findall('.//PropertyText'):
                text_type = prop_text.get('type')
                if text_type == 'Content' and prop_text.text:
                    wz2008_code = prop_text.text.strip()
                elif text_type == 'Example' and prop_text.text:
                    is_partial = prop_text.text.strip() == 'ex'

            if wz2008_code:
                correspondences.append((wz2008_code, is_partial))

                # Build reverse mapping
                if wz2008_code not in reverse_map:
                    reverse_map[wz2008_code] = []
                if wz2025_code not in reverse_map[wz2008_code]:
                    reverse_map[wz2008_code].append(wz2025_code)

        if correspondences:
            forward_map[wz2025_code] = correspondences

    print(f"  Forward mappings: {len(forward_map)} WZ 2025 codes")
    print(f"  Reverse mappings: {len(reverse_map)} WZ 2008 codes")

    # Count partial vs full
    total_correspondences = sum(len(corrs) for corrs in forward_map.values())
    partial_count = sum(1 for corrs in forward_map.values() for _, is_partial in corrs if is_partial)
    print(f"  Total correspondences: {total_correspondences}")
    print(f"    Full: {total_correspondences - partial_count}")
    print(f"    Partial: {partial_count}")

    return forward_map, reverse_map


def generate_python_module(
    data: dict[str, dict[str, Any]], version: str, output_path: Path
) -> None:
    """Generate a Python module from WZ data.

    Args:
        data: Dictionary mapping code -> data entry.
        version: WZ version ("2008" or "2025").
        output_path: Path where the Python module will be written.

    Example:
        >>> data = {"A": {"l": 1, "t": "Agriculture", "p": None, "c": ["01"]}}
        >>> generate_python_module(data, "2025", Path("wz_code/data/wz2025.py"))
    """
    print(f"Generating Python module for WZ {version} at {output_path}...")

    # Format data as Python dict literal
    lines = [
        '"""',
        f"WZ {version} classification data (auto-generated from XML).",
        "",
        "DO NOT EDIT THIS FILE MANUALLY.",
        'Generated by: python -m wz_code._build.generator',
        '"""',
        "",
        "from typing import Any",
        "",
        f"WZ_{version}_DATA: dict[str, dict[str, Any]] = {{",
    ]

    # Sort codes for consistent output
    for code in sorted(data.keys()):
        entry = data[code]
        lines.append(f'    "{code}": {{')
        lines.append(f'        "l": {entry["l"]},')
        lines.append(f'        "t": {repr(entry["t"])},')
        lines.append(f'        "p": {repr(entry["p"])},')

        # Format children list
        if entry["c"]:
            children_str = ", ".join(f'"{c}"' for c in entry["c"])
            lines.append(f'        "c": [{children_str}],')
        else:
            lines.append('        "c": None,')

        lines.append("    },")

    lines.append("}")
    lines.append("")

    # Write to file
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Generated {len(data)} codes")


def generate_correspondence_module(
    forward_map: dict[str, list[tuple[str, bool]]],
    reverse_map: dict[str, list[str]],
    wz2008_data: dict[str, dict[str, Any]],
    wz2025_data: dict[str, dict[str, Any]],
    output_path: Path,
) -> None:
    """Generate a Python module for correspondence mappings.

    Args:
        forward_map: WZ 2025 -> WZ 2008 correspondences.
        reverse_map: WZ 2008 -> WZ 2025 correspondences.
        wz2008_data: WZ 2008 classification data (for titles).
        wz2025_data: WZ 2025 classification data (for titles).
        output_path: Path where the Python module will be written.
    """
    print(f"Generating correspondence module at {output_path}...")

    lines = [
        '"""',
        "WZ 2025 ↔ WZ 2008 correspondence mappings (auto-generated from XML).",
        "",
        "This module contains bidirectional mappings between WZ 2025 and WZ 2008",
        "classification codes, including information about partial vs. full matches.",
        "",
        "DO NOT EDIT THIS FILE MANUALLY.",
        'Generated by: python -m wz_code._build.generator',
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "# Forward mapping: WZ 2025 code -> list of (WZ 2008 code, is_partial, title)",
        "CORRESPONDENCES_2025_TO_2008: dict[str, list[tuple[str, bool, str]]] = {",
    ]

    # Generate forward mappings (sorted by WZ 2025 code)
    for wz2025_code in sorted(forward_map.keys()):
        correspondences = forward_map[wz2025_code]
        lines.append(f'    "{wz2025_code}": [')

        for wz2008_code, is_partial in correspondences:
            # Get title from WZ 2008 data
            title = wz2008_data.get(wz2008_code, {}).get("t", "")
            lines.append(f'        ("{wz2008_code}", {is_partial}, {repr(title)}),')

        lines.append("    ],")

    lines.append("}")
    lines.append("")

    # Generate reverse mappings
    lines.append("# Reverse mapping: WZ 2008 code -> list of (WZ 2025 code, title)")
    lines.append("CORRESPONDENCES_2008_TO_2025: dict[str, list[tuple[str, str]]] = {")

    for wz2008_code in sorted(reverse_map.keys()):
        wz2025_codes = reverse_map[wz2008_code]
        lines.append(f'    "{wz2008_code}": [')

        for wz2025_code in wz2025_codes:
            # Get title from WZ 2025 data
            title = wz2025_data.get(wz2025_code, {}).get("t", "")
            lines.append(f'        ("{wz2025_code}", {repr(title)}),')

        lines.append("    ],")

    lines.append("}")
    lines.append("")

    # Write to file
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Generated {len(forward_map)} forward + {len(reverse_map)} reverse mappings")


def main() -> None:
    """Main entry point for data generation."""
    parser = argparse.ArgumentParser(
        description="Generate WZ data modules from XML files"
    )
    parser.add_argument(
        "--wz2025",
        type=Path,
        required=True,
        help="Path to WZ 2025 XML file"
    )
    parser.add_argument(
        "--wz2008",
        type=Path,
        required=True,
        help="Path to WZ 2008 XML file"
    )
    parser.add_argument(
        "--correspondences",
        type=Path,
        required=False,
        help="Path to correspondences XML file (optional)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent.parent / "data",
        help="Output directory for generated modules",
    )

    args = parser.parse_args()

    # Validate input files
    if not args.wz2025.exists():
        raise FileNotFoundError(f"WZ 2025 file not found: {args.wz2025}")
    if not args.wz2008.exists():
        raise FileNotFoundError(f"WZ 2008 file not found: {args.wz2008}")

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Generate WZ 2025 module
    wz2025_data = read_wz_xml(args.wz2025)
    generate_python_module(wz2025_data, "2025", args.output / "wz2025.py")

    # Generate WZ 2008 module
    wz2008_data = read_wz_xml(args.wz2008)
    generate_python_module(wz2008_data, "2008", args.output / "wz2008.py")

    # Generate correspondence module if provided
    if args.correspondences:
        if not args.correspondences.exists():
            raise FileNotFoundError(f"Correspondence file not found: {args.correspondences}")

        forward_map, reverse_map = read_correspondence_xml(args.correspondences)
        generate_correspondence_module(
            forward_map,
            reverse_map,
            wz2008_data,
            wz2025_data,
            args.output / "correspondences.py"
        )

    print("\nData generation complete!")
    print(f"  WZ 2025: {len(wz2025_data)} codes")
    print(f"  WZ 2008: {len(wz2008_data)} codes")
    if args.correspondences:
        print(f"  Correspondences: Generated bidirectional mappings")


if __name__ == "__main__":
    main()
