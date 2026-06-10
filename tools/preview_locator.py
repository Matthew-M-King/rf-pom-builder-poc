#!/usr/bin/env python3
"""Preview the locator that Build Locator would produce for a given element.

Replicates LocatorBuilder.robot dispatch logic in pure Python — no Robot Framework
dependency and no browser required.

Usage:
    python tools/preview_locator.py <target_app> <page> <element>
    python tools/preview_locator.py <target_app> <page> --all

Examples:
    python tools/preview_locator.py SwagLabs LoginPage LoginButton
    python tools/preview_locator.py SwagLabs ProductsPage --all
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target_app", help="App name (e.g. SwagLabs)")
    parser.add_argument("page", help="Page name (e.g. LoginPage)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("element", nargs="?", help="Element name (e.g. LoginButton)")
    group.add_argument("--all", action="store_true", dest="show_all", help="Show all elements on the page")
    args = parser.parse_args()

    page_objects = _load_page(args.target_app, args.page)
    if page_objects is None:
        sys.exit(1)

    if args.show_all:
        for name in sorted(page_objects):
            _print_element(args.target_app, args.page, name, page_objects)
            print()
    else:
        _print_element(args.target_app, args.page, args.element, page_objects)


def _load_page(target_app: str, page: str) -> dict | None:
    yaml_path = _ROOT / "Resources" / "PO" / "ObjectRegistry" / target_app / f"{page}.yaml"
    if not yaml_path.exists():
        print(f"Error: {yaml_path.relative_to(_ROOT)} not found", file=sys.stderr)
        return None
    with open(yaml_path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    objects_key = f"{page}_Objects"
    if objects_key not in data:
        print(f"Error: expected top-level key '{objects_key}' in {yaml_path.name}", file=sys.stderr)
        return None
    return data[objects_key] or {}


def _print_element(target_app: str, page: str, element: str, page_objects: dict) -> None:
    if element not in page_objects:
        available = ", ".join(sorted(page_objects))
        print(f"Error: '{element}' not found in {page}.yaml\nAvailable: {available}", file=sys.stderr)
        sys.exit(1)

    props = page_objects[element] or {}
    strategy = props.get("LocatorStrategy", "(missing)")

    print("---")
    print(f"Target App : {target_app}")
    print(f"Page       : {page}")
    print(f"Element    : {element}")
    print(f"Strategy   : {strategy}")
    print("Generated Locator:")

    try:
        locator = _build_locator(page_objects, element)
        print(f"  {locator}")
    except _BrowserRequired:
        group_ref = props.get("GroupReference", "")
        print("  (runtime only - SelectFromGroupByCSSProperty requires an active browser)")
        if group_ref and group_ref in page_objects:
            group_locator = _build_locator(page_objects, group_ref)
            print(f"  Group reference resolves to: {group_locator}")
    except Exception as exc:
        print(f"  (error: {exc})", file=sys.stderr)

    print("---")


def _build_locator(page_objects: dict, element_name: str) -> str:
    props = page_objects[element_name] or {}
    strategy: str = props.get("LocatorStrategy", "")

    if strategy.startswith("ParentReference"):
        base_strategy = strategy[len("ParentReference"):]
        parent_ref = props.get("ParentReference", "")
        parent_locator = _build_locator(page_objects, parent_ref)
        child_locator = _build_single(base_strategy, props)
        return parent_locator + child_locator

    return _build_single(strategy, props)


def _build_single(strategy: str, props: dict) -> str:
    axes = _build_axes(props)

    if strategy == "XPathLookup":
        return axes + props["Xpath"]
    if strategy == "WithAttribute":
        t, attr, name = props["ElementType"], props["Attribute"], props["Name"]
        return f'{axes}//{t}[@{attr}="{name}"]'
    if strategy == "WithText":
        t, text = props["ElementType"], props["Text"]
        return f'{axes}//{t}[normalize-space()="{text}"]'
    if strategy == "WithContainsAttribute":
        t, attr, name = props["ElementType"], props["Attribute"], props["Name"]
        return f'{axes}//{t}[contains(@{attr}, "{name}")]'
    if strategy == "WithType":
        return f'{axes}//{props["ElementType"]}'
    if strategy == "SelectFromGroupByCSSProperty":
        raise _BrowserRequired()
    raise ValueError(f"Unknown strategy: {strategy!r}")


def _build_axes(props: dict) -> str:
    if props.get("UseRelation"):
        return f'//{props["Relation"]}::{props["RelationElementType"]}'
    return ""


class _BrowserRequired(Exception):
    pass


if __name__ == "__main__":
    main()
