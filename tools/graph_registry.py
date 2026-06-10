#!/usr/bin/env python3
"""Print a structured overview of the object and definition registries for an app.

Useful for understanding which pages exist, which elements are defined, which locator
strategies are in use, and what assertions are configured per environment.

Usage:
    python tools/graph_registry.py <target_app> [environment]

Examples:
    python tools/graph_registry.py SwagLabs
    python tools/graph_registry.py SwagLabs Staging
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent

_STRATEGY_ABBREV = {
    "XPathLookup": "XPath",
    "WithAttribute": "Attr",
    "WithText": "Text",
    "WithContainsAttribute": "ContainsAttr",
    "WithType": "Type",
    "SelectFromGroupByCSSProperty": "CSS",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target_app", help="App name (e.g. SwagLabs)")
    parser.add_argument("environment", nargs="?", help="Environment to show definitions for (e.g. Staging)")
    args = parser.parse_args()

    objects_by_page = _load_object_registry(args.target_app)
    if not objects_by_page:
        print(f"No ObjectRegistry found for '{args.target_app}'.", file=sys.stderr)
        sys.exit(1)

    _print_object_registry(args.target_app, objects_by_page)

    if args.environment:
        defs_by_page = _load_definitions(args.target_app, args.environment)
        if defs_by_page:
            print()
            _print_definitions(args.target_app, args.environment, defs_by_page)
        else:
            print(f"\n(No definitions found for {args.target_app}/{args.environment})")
    else:
        envs = _available_environments(args.target_app)
        if envs:
            print(f"\nPass an environment to see definitions: {' | '.join(envs)}")


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def _load_object_registry(target_app: str) -> dict[str, dict]:
    base = _ROOT / "Resources" / "PO" / "ObjectRegistry" / target_app
    if not base.exists():
        return {}
    result: dict[str, dict] = {}
    for yaml_file in sorted(base.glob("*.yaml")):
        page = yaml_file.stem
        data = _load_yaml(yaml_file)
        objects = data.get(f"{page}_Objects") or {}
        result[page] = objects
    return result


def _load_definitions(target_app: str, environment: str) -> dict[str, dict]:
    base = _ROOT / "Settings" / "DataSets" / target_app / environment
    if not base.exists():
        return {}
    result: dict[str, dict] = {}
    for yaml_file in sorted(base.glob("*Definitions.yaml")):
        page = yaml_file.stem.replace("Definitions", "")
        data = _load_yaml(yaml_file)
        defs = data.get(f"{page}_Definitions") or {}
        result[page] = defs
    return result


def _available_environments(target_app: str) -> list[str]:
    base = _ROOT / "Settings" / "DataSets" / target_app
    if not base.exists():
        return []
    return sorted(d.name for d in base.iterdir() if d.is_dir())


# ---------------------------------------------------------------------------
# Printers
# ---------------------------------------------------------------------------

def _print_object_registry(target_app: str, objects_by_page: dict[str, dict]) -> None:
    total_objects = sum(len(v) for v in objects_by_page.values())
    header = f"{target_app} - Object Registry  ({len(objects_by_page)} pages, {total_objects} objects)"
    print(header)
    print("=" * len(header))

    for page, objects in objects_by_page.items():
        print(f"\n  {page}  ({len(objects)} objects)")
        if not objects:
            print("    (empty)")
            continue
        name_width = max(len(n) for n in objects) + 2
        for name, props in objects.items():
            props = props or {}
            strategy = props.get("LocatorStrategy", "(missing)")
            detail = _strategy_detail(strategy, props, objects)
            abbrev = _STRATEGY_ABBREV.get(
                strategy if not strategy.startswith("ParentReference") else "PARENT",
                strategy,
            )
            if strategy.startswith("ParentReference"):
                base = strategy[len("ParentReference"):]
                abbrev = f"Parent+{_STRATEGY_ABBREV.get(base, base)}"
            print(f"    {name:<{name_width}} {abbrev:<18} {detail}")


def _strategy_detail(strategy: str, props: dict, page_objects: dict) -> str:
    if strategy == "XPathLookup":
        return props.get("Xpath", "")[:60]
    if strategy in ("WithAttribute", "WithContainsAttribute"):
        return f'[@{props.get("Attribute")}="{props.get("Name")}"]'
    if strategy == "WithText":
        return f'"{props.get("Text")}"'
    if strategy == "WithType":
        return f'//{props.get("ElementType")}'
    if strategy == "SelectFromGroupByCSSProperty":
        return f'{props.get("CSSPropertyType")}={props.get("PropertyValue")}'
    if strategy.startswith("ParentReference"):
        parent = props.get("ParentReference", "?")
        return f"parent: {parent}"
    return ""


def _print_definitions(target_app: str, environment: str, defs_by_page: dict[str, dict]) -> None:
    total_defs = sum(len(v) for v in defs_by_page.values())
    header = f"{target_app}/{environment} - Definitions  ({len(defs_by_page)} pages, {total_defs} assertions)"
    print(header)
    print("=" * len(header))

    for page, defs in defs_by_page.items():
        print(f"\n  {page}  ({len(defs)} elements)")
        if not defs:
            print("    (empty)")
            continue
        name_width = max(len(n) for n in defs) + 2
        for name, props in defs.items():
            props = props or {}
            parts = []
            for key, value in props.items():
                if isinstance(value, list):
                    parts.append(f"{key}: [{', '.join(str(v) for v in value[:3])}{'...' if len(value) > 3 else ''}]")
                elif isinstance(value, dict):
                    parts.append(f"{key}: ({len(value)} entries)")
                else:
                    parts.append(f"{key}: {value}")
            print(f"    {name:<{name_width}} {', '.join(parts)}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


if __name__ == "__main__":
    main()
