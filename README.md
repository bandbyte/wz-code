# wz-code

High-performance Python package for working with German economic activity classifications (Wirtschaftszweigklassifikation).

## Features

- **Zero Configuration**: Install and start using immediately
- **High Performance**: Sub-millisecond lookups, optimized memory usage
- **Complete Data**: Embedded WZ 2008 and WZ 2025 classifications
- **Bidirectional Correspondences**: Map between WZ 2025 and WZ 2008 versions
- **CLI Tool**: Use directly from command line
- **Type Safe**: Full type hints for IDE support
- **Python 3.8+**: Modern Python with backward compatibility

## Installation

```bash
pip install wz-code
```

## Quick Start

```python
from wz_code import WZ

# Initialize with WZ 2025
wz = WZ(version="2025")

# Get a specific code
agriculture = wz.get("A")
print(agriculture.title)
# Output: Land- und Forstwirtschaft, Fischerei

# Navigate hierarchy
for child in agriculture.children:
    print(f"{child.code}: {child.title}")

# Works with WZ 2008 too (full hierarchical structure)
wz2008 = WZ(version="2008")
code = wz2008.get("01.11.0")
print(f"Code: {code.code}, Level: {code.level}")
print(f"Ancestors: {[a.code for a in code.ancestors]}")

# Find correspondences between WZ versions
wz = WZ(version="2025")
code = wz.get("01.13.1")
correspondences = code.correspondences

for corr in correspondences:
    match_type = "partial" if corr.is_partial else "full"
    print(f"{corr.code}: {corr.title} ({match_type} match)")
# Output:
# 01.13.1: Anbau von Gemüse und Melonen (full match)
# 01.19.9: Anbau von sonstigen einjährigen Pflanzen a. n. g. (partial match)
# 01.28.0: Anbau von Gewürzpflanzen... (partial match)
```

## Command-Line Interface

The package includes a CLI tool for quick lookups and exploration:

### Get code information

```bash
# Get info about a code
wz-code get A

# Use WZ 2008
wz-code get 01.11 -v 2008

# Output as JSON
wz-code get A --json
```

### Search for codes

```bash
# Search in titles
wz-code search "Landwirtschaft"

# Limit results
wz-code search "Herstellung" --limit 10

# Case-sensitive search
wz-code search "LAND" --case-sensitive
```

### List codes

```bash
# List top-level codes
wz-code list --top-level

# List codes at specific level
wz-code list --level 2

# List with hierarchy indentation
wz-code list --indent
```

### Display tree view

```bash
# Show full tree for a code
wz-code tree A

# Limit depth
wz-code tree A --depth 2

# JSON tree output
wz-code tree 01 --json
```

### Map between WZ versions

```bash
# Show correspondences for a code
wz-code map 01.13.1

# Works with WZ 2008 too
wz-code map 01.19.9 -v 2008

# JSON output
wz-code map 01.13.1 --json
```

## Development

Install in development mode:

```bash
poetry install --with dev
```

Run tests:

```bash
poetry run pytest
```

Generate data modules from XML sources:

```bash
poetry run python -m wz_code._build.generator \
  --wz2025 source/WZ_2025_DE_2025-08-19.xml \
  --wz2008 source/WZ_2008_DE_2025-09-29.xml \
  --correspondences source/WZ2025-2025-08-19-Correspondences.xml
```

## License

MIT License - see LICENSE file for details.
