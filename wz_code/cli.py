"""Command-line interface for wz-code package."""

import argparse
import json
import sys
from typing import Any

from wz_code import WZ, WZCode, WZCodeNotFoundError
from wz_code.models import WZVersion


def format_code_info(code: WZCode, verbose: bool = False) -> dict[str, Any]:
    """Format code information for output.

    Args:
        code: WZCode instance to format.
        verbose: Include additional details.

    Returns:
        Dictionary with code information.
    """
    info: dict[str, Any] = {
        "code": code.code,
        "title": code.title,
        "level": code.level,
        "version": code.version,
    }

    if verbose:
        info["parent"] = code.parent.code if code.parent else None
        info["children"] = [c.code for c in code.children]
        info["ancestors"] = [a.code for a in code.ancestors]
        info["descendant_count"] = len(code.descendants)

    return info


def print_code_info(code: WZCode, verbose: bool = False) -> None:
    """Print code information in human-readable format.

    Args:
        code: WZCode instance to print.
        verbose: Include additional details.
    """
    print(f"Code: {code.code}")
    print(f"Title: {code.title}")
    print(f"Level: {code.level}")
    print(f"Version: WZ {code.version}")

    if verbose or code.parent or code.children:
        print()
        if code.parent:
            print(f"Parent: {code.parent.code} - {code.parent.title}")

        if code.children:
            print(f"Children ({len(code.children)}):")
            for child in code.children:
                print(f"  {child.code}: {child.title}")


def cmd_get(args: argparse.Namespace) -> int:
    """Handle 'get' command - lookup a specific code.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    try:
        wz = WZ(version=args.version)
        code = wz.get(args.code)

        if args.json:
            print(json.dumps(format_code_info(code, verbose=True), indent=2, ensure_ascii=False))
        else:
            print_code_info(code, verbose=True)

        return 0

    except WZCodeNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_search(args: argparse.Namespace) -> int:
    """Handle 'search' command - search for codes by title.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success).
    """
    wz = WZ(version=args.version)
    results = wz.search_in_titles(args.query, case_sensitive=args.case_sensitive)

    # Limit results if specified
    if args.limit:
        results = results[: args.limit]

    if args.json:
        output = [format_code_info(code) for code in results]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"Found {len(results)} results in WZ {args.version}:")
        print()
        for result in results:
            print(f"  {result.code}: {result.title}")

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """Handle 'list' command - list codes.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success).
    """
    wz = WZ(version=args.version)

    if args.top_level:
        codes = wz.get_top_level_codes()
        title = f"Top-level codes (Level 1) in WZ {args.version}"
    elif args.level:
        all_codes = [wz.get(c) for c in wz.get_all_codes()]
        codes = [c for c in all_codes if c.level == args.level]
        title = f"Codes at Level {args.level} in WZ {args.version}"
    else:
        codes = [wz.get(c) for c in wz.get_all_codes()]
        title = f"All codes in WZ {args.version}"

    if args.json:
        output = [format_code_info(code) for code in codes]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"{title} ({len(codes)} codes):")
        print()
        for code in codes:
            indent = "  " * (code.level - 1) if args.indent else ""
            print(f"{indent}{code.code}: {code.title}")

    return 0


def cmd_tree(args: argparse.Namespace) -> int:
    """Handle 'tree' command - display hierarchical tree.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    try:
        wz = WZ(version=args.version)
        root_code = wz.get(args.code)

        if args.json:
            def build_tree(code: WZCode, max_depth: int | None = None, current_depth: int = 0) -> dict[str, Any]:
                tree: dict[str, Any] = format_code_info(code)
                if max_depth is None or current_depth < max_depth:
                    tree["children_tree"] = [
                        build_tree(child, max_depth, current_depth + 1)
                        for child in code.children
                    ]
                return tree

            output = build_tree(root_code, args.depth)
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            def print_tree(code: WZCode, prefix: str = "", max_depth: int | None = None, current_depth: int = 0) -> None:
                print(f"{prefix}{code.code}: {code.title}")
                if max_depth is None or current_depth < max_depth:
                    for i, child in enumerate(code.children):
                        is_last = i == len(code.children) - 1
                        child_prefix = prefix + ("└── " if is_last else "├── ")
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        print(f"{child_prefix}{child.code}: {child.title}")
                        if child.children and (max_depth is None or current_depth + 1 < max_depth):
                            for j, grandchild in enumerate(child.children):
                                is_last_gc = j == len(child.children) - 1
                                gc_prefix = next_prefix + ("└── " if is_last_gc else "├── ")
                                print(f"{gc_prefix}{grandchild.code}: {grandchild.title}")

            print(f"Tree for {root_code.code} (WZ {args.version}):")
            print()
            print_tree(root_code, max_depth=args.depth)

        return 0

    except WZCodeNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_map(args: argparse.Namespace) -> int:
    """Handle 'map' command - show correspondences to other WZ version.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    try:
        wz = WZ(version=args.version)
        code = wz.get(args.code)
        correspondences = code.correspondences

        if args.json:
            output = {
                "code": code.code,
                "title": code.title,
                "version": code.version,
                "target_version": "2008" if code.version == "2025" else "2025",
                "correspondences": [
                    {
                        "code": corr.code,
                        "title": corr.title,
                        "is_partial": corr.is_partial,
                        "version": corr.version,
                    }
                    for corr in correspondences
                ],
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            target_version = "2008" if code.version == "2025" else "2025"
            print(f"Code: {code.code} (WZ {code.version})")
            print(f"Title: {code.title}")
            print()

            if not correspondences:
                print(f"No correspondences to WZ {target_version} found.")
            else:
                print(f"Maps to WZ {target_version}:")
                print()
                for corr in correspondences:
                    match_type = "partial" if corr.is_partial else "full"
                    symbol = "~" if corr.is_partial else "✓"
                    print(f"  {symbol} {corr.code}: {corr.title}")
                    print(f"    ({match_type} match)")

                # Summary
                full_count = sum(1 for c in correspondences if not c.is_partial)
                partial_count = sum(1 for c in correspondences if c.is_partial)
                print()
                print(f"Total: {len(correspondences)} correspondence(s)")
                if full_count:
                    print(f"  Full matches: {full_count}")
                if partial_count:
                    print(f"  Partial matches: {partial_count}")

        return 0

    except WZCodeNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        prog="wz-code",
        description="German economic classification (WZ) lookup tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  wz-code get A                    # Get info about code A
  wz-code search "Landwirtschaft"  # Search for codes
  wz-code list --top-level         # List top-level codes
  wz-code tree A --depth 2         # Show tree view
  wz-code map 01.13.1              # Show correspondences to other WZ version
  wz-code get 01.11 --json         # Output as JSON
        """,
    )

    parser.add_argument(
        "--version-info",
        action="version",
        version="%(prog)s 0.1.0",
        help="Show version information",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Common arguments for all commands
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "-v",
        "--wz-version",
        dest="version",
        choices=["2008", "2025"],
        default="2025",
        help="WZ version to use (default: 2025)",
    )
    common_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    # 'get' command
    parser_get = subparsers.add_parser(
        "get",
        parents=[common_parser],
        help="Get information about a specific WZ code",
        description="Lookup a WZ code and display its details including parent and children.",
    )
    parser_get.add_argument("code", help="WZ code to lookup (e.g., A, 01, 01.11)")

    # 'search' command
    parser_search = subparsers.add_parser(
        "search",
        parents=[common_parser],
        help="Search for codes by title",
        description="Search for WZ codes by substring match in titles.",
    )
    parser_search.add_argument("query", help="Search query")
    parser_search.add_argument(
        "-c",
        "--case-sensitive",
        action="store_true",
        help="Case-sensitive search",
    )
    parser_search.add_argument(
        "-l",
        "--limit",
        type=int,
        help="Limit number of results",
    )

    # 'list' command
    parser_list = subparsers.add_parser(
        "list",
        parents=[common_parser],
        help="List WZ codes",
        description="List all codes or filter by level.",
    )
    parser_list.add_argument(
        "-t",
        "--top-level",
        action="store_true",
        help="List only top-level codes (Level 1)",
    )
    parser_list.add_argument(
        "-l",
        "--level",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="List codes at specific level",
    )
    parser_list.add_argument(
        "--indent",
        action="store_true",
        help="Indent codes based on hierarchy level",
    )

    # 'tree' command
    parser_tree = subparsers.add_parser(
        "tree",
        parents=[common_parser],
        help="Display hierarchical tree view",
        description="Display a tree view of a code and its descendants.",
    )
    parser_tree.add_argument("code", help="Root code for tree view")
    parser_tree.add_argument(
        "-d",
        "--depth",
        type=int,
        help="Maximum depth to display (default: unlimited)",
    )

    # 'map' command
    parser_map = subparsers.add_parser(
        "map",
        parents=[common_parser],
        help="Show correspondences to other WZ version",
        description="Display correspondences between WZ 2025 and WZ 2008 versions.",
    )
    parser_map.add_argument("code", help="WZ code to get correspondences for")

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 0

    # Execute command
    if args.command == "get":
        return cmd_get(args)
    elif args.command == "search":
        return cmd_search(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "tree":
        return cmd_tree(args)
    elif args.command == "map":
        return cmd_map(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
