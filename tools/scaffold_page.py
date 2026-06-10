#!/usr/bin/env python3
"""Generate boilerplate for a new page in an existing app.

Creates or updates the following files (skips files that already exist or
already contain the relevant entry):

  Resources/PO/ObjectRegistry/{App}/{Page}.yaml          [new]
  Resources/PO/PageRegistry/_{App}Variables.robot        [+Variables line]
  Settings/DataSets/{App}/{Env}/{Page}Definitions.yaml   [new, per env]
  Settings/DataSets/{App}/{Env}/_DatasetRegistry.robot   [+Variables line, per env]
  Settings/DataSets/{App}/{Env}/UrlRegistry.yaml         [+URL entry, per env]

Usage:
    python tools/scaffold_page.py <target_app> <page_name> [--url <url-fragment>]

Examples:
    python tools/scaffold_page.py SwagLabs CheckoutPage
    python tools/scaffold_page.py SwagLabs CheckoutPage --url checkout-step-one
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent
_PLACEHOLDER_URL = "PLACEHOLDER"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target_app")
    parser.add_argument("page_name")
    parser.add_argument("--url", default=_PLACEHOLDER_URL, metavar="fragment",
                        help="URL fragment appended to BaseUrl (default: PLACEHOLDER)")
    args = parser.parse_args()

    target_app, page_name, url = args.target_app, args.page_name, args.url

    _check_app_exists(target_app)

    print(f"Scaffolding {target_app}/{page_name}...\n")
    actions: list[tuple[str, str, str | None]] = []

    _scaffold_object_registry(target_app, page_name, actions)
    _update_page_registry(target_app, page_name, actions)
    _scaffold_environments(target_app, page_name, url, actions)

    _print_actions(actions)
    _print_next_steps(target_app, page_name, url)


# ---------------------------------------------------------------------------
# Scaffolding steps
# ---------------------------------------------------------------------------

def _scaffold_object_registry(target_app: str, page_name: str, actions: list) -> None:
    path = _ROOT / "Resources" / "PO" / "ObjectRegistry" / target_app / f"{page_name}.yaml"
    if path.exists():
        actions.append(("SKIP", path, "already exists"))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"{page_name}_Objects:\n"
        f"  # Add locator definitions here. Supported strategies:\n"
        f"  # XPathLookup, WithAttribute, WithText, WithContainsAttribute,\n"
        f"  # WithType, ParentReference{{Strategy}}, SelectFromGroupByCSSProperty\n"
        f"  #\n"
        f"  # Example:\n"
        f"  #   SubmitButton:\n"
        f"  #     LocatorStrategy: XPathLookup\n"
        f"  #     Xpath: //button[@type='submit']\n",
        encoding="utf-8",
    )
    actions.append(("NEW", path, None))


def _update_page_registry(target_app: str, page_name: str, actions: list) -> None:
    path = _ROOT / "Resources" / "PO" / "PageRegistry" / f"_{target_app}Variables.robot"
    if not path.exists():
        actions.append(("WARN", path, "file not found — create it manually"))
        return
    content = path.read_text(encoding="utf-8")
    # Check by filename only — the existing file may use different whitespace
    if f"/{page_name}.yaml" in content:
        actions.append(("SKIP", path, "entry already present"))
        return
    new_line = f"Variables  ../ObjectRegistry/${{target_app}}/{page_name}.yaml"
    _append_line(path, content, new_line)
    actions.append(("UPD", path, "+1 Variables line"))


def _scaffold_environments(target_app: str, page_name: str, url: str, actions: list) -> None:
    env_base = _ROOT / "Settings" / "DataSets" / target_app
    if not env_base.exists():
        actions.append(("WARN", env_base, "no DataSets folder found for this app"))
        return

    envs = sorted(d.name for d in env_base.iterdir() if d.is_dir())
    if not envs:
        actions.append(("WARN", env_base, "no environment folders found"))
        return

    for env in envs:
        env_dir = env_base / env
        _scaffold_definitions(env_dir, page_name, actions)
        _update_dataset_registry(env_dir, page_name, actions)
        _update_url_registry(env_dir, page_name, url, actions)


def _scaffold_definitions(env_dir: Path, page_name: str, actions: list) -> None:
    path = env_dir / f"{page_name}Definitions.yaml"
    if path.exists():
        actions.append(("SKIP", path, "already exists"))
        return
    path.write_text(
        f"{page_name}_Definitions:\n"
        f"  # Keys must match {page_name}_Objects entries exactly.\n"
        f"  # Supported assertion properties:\n"
        f"  #   ElementCountShouldBe, ShouldContain, EachInGroupShouldContain,\n"
        f"  #   TableContentShouldBe, ImageGroupAttributes\n"
        f"  #\n"
        f"  # Example:\n"
        f"  #   SubmitButton:\n"
        f"  #     ElementCountShouldBe: 1\n",
        encoding="utf-8",
    )
    actions.append(("NEW", path, None))


def _update_dataset_registry(env_dir: Path, page_name: str, actions: list) -> None:
    path = env_dir / "_DatasetRegistry.robot"
    if not path.exists():
        actions.append(("WARN", path, "file not found — create it manually"))
        return
    content = path.read_text(encoding="utf-8")
    new_line = f"Variables  {page_name}Definitions.yaml"
    # Check by filename only — the existing file may use different whitespace
    if f"{page_name}Definitions.yaml" in content:
        actions.append(("SKIP", path, "entry already present"))
        return
    # Insert before UrlRegistry line to keep definitions grouped together
    if "Variables  UrlRegistry.yaml" in content:
        updated = content.replace(
            "Variables  UrlRegistry.yaml",
            f"{new_line}\nVariables  UrlRegistry.yaml",
        )
        path.write_text(updated, encoding="utf-8")
    else:
        _append_line(path, content, new_line)
    actions.append(("UPD", path, "+1 Variables line"))


def _update_url_registry(env_dir: Path, page_name: str, url: str, actions: list) -> None:
    path = env_dir / "UrlRegistry.yaml"
    if not path.exists():
        actions.append(("WARN", path, "file not found — create it manually"))
        return
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    urls_to_pages = data.get("UrlsToPages", {}) or {}
    if page_name in urls_to_pages:
        actions.append(("SKIP", path, f"'{page_name}' entry already present"))
        return
    urls_to_pages[page_name] = url
    data["UrlsToPages"] = urls_to_pages
    with open(path, "w", encoding="utf-8") as fh:
        yaml.dump(data, fh, default_flow_style=False, sort_keys=False, indent=4, allow_unicode=True)
    actions.append(("UPD", path, f"+1 URL entry ({url})"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_app_exists(target_app: str) -> None:
    import importlib.util
    registry = _ROOT / "Settings" / "AppRegistry.py"
    spec = importlib.util.spec_from_file_location("AppRegistry", registry)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    try:
        mod.get_variables(target_app)
    except Exception:
        print(f"Error: '{target_app}' is not registered in Settings/AppRegistry.py", file=sys.stderr)
        sys.exit(1)


def _append_line(path: Path, existing_content: str, line: str) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        if not existing_content.endswith("\n"):
            fh.write("\n")
        fh.write(line + "\n")


def _print_actions(actions: list) -> None:
    label = {"NEW": "[NEW] ", "UPD": "[UPD] ", "SKIP": "[---] ", "WARN": "[!!!] "}
    for action, path, note in actions:
        rel = str(path.relative_to(_ROOT)) if isinstance(path, Path) else str(path)
        suffix = f"  ({note})" if note else ""
        print(f"  {label[action]}{rel}{suffix}")
    print()


def _print_next_steps(target_app: str, page_name: str, url: str) -> None:
    steps = [
        f"Add locator definitions to Resources/PO/ObjectRegistry/{target_app}/{page_name}.yaml",
        f"Add assertion definitions to Settings/DataSets/{target_app}/*/{page_name}Definitions.yaml",
    ]
    if url == _PLACEHOLDER_URL:
        steps.append("Replace PLACEHOLDER in each UrlRegistry.yaml with the actual URL fragment")
    steps.append(f"Run: python Settings/YamlValidator.py {target_app} Staging")

    print("Next steps:")
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}")


if __name__ == "__main__":
    main()
