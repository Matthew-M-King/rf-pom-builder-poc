"""YAML registry validator for the RF POM framework.

Can be used two ways:
  - As a Robot Framework library: ``Library    ../Settings/YamlValidator.py``
    then call ``Validate Registry    ${target_app}    ${environment}``
  - As a standalone CLI check (used by CI validate stage):
    ``python Settings/YamlValidator.py SwagLabs Staging``
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

# robot.api is only needed when running inside Robot Framework.
# Importing it at module level would break the plain-Python CLI path on
# environments where Robot is not installed (e.g. a bare lint/validate image).
try:
    from robot.api.deco import keyword as _rf_keyword
except ImportError:  # pragma: no cover
    def _rf_keyword(name: str):           # type: ignore[misc]
        """No-op decorator when Robot Framework is not available."""
        def decorator(fn):
            return fn
        return decorator

# ---------------------------------------------------------------------------
# Strategy → required fields (non-optional fields only).
# ParentReference* strategies prepend 'ParentReference' to their base fields.
# UseRelation / Relation / RelationElementType are always optional.
# ---------------------------------------------------------------------------
_BASE_STRATEGY_FIELDS: dict[str, list[str]] = {
    "XPathLookup": ["Xpath"],
    "WithAttribute": ["ElementType", "Attribute", "Name"],
    "WithText": ["ElementType", "Text"],
    "WithContainsAttribute": ["ElementType", "Attribute", "Name"],
    "WithType": ["ElementType"],
    "SelectFromGroupByCSSProperty": ["GroupReference", "CSSPropertyType", "PropertyValue"],
}

# Strategies that support a ParentReference prefix
_PARENT_REF_ELIGIBLE = {s for s in _BASE_STRATEGY_FIELDS if s != "SelectFromGroupByCSSProperty"}

# Assertion property keys dispatched by _AssertDefinitions.robot
_SUPPORTED_ASSERTION_PROPS = {
    "ElementCountShouldBe",
    "ShouldContain",
    "EachInGroupShouldContain",
    "TableContentShouldBe",
    "ImageGroupAttributes",
    "ElementGroup",  # present in some YAMLs; not dispatched but tolerated
}


class YamlValidator:
    """Validates all YAML registries for a given app and environment."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self) -> None:
        # Resolve project root relative to this file's location (Settings/)
        self._root = Path(__file__).resolve().parent.parent

    # ------------------------------------------------------------------
    # Public RF keyword
    # ------------------------------------------------------------------

    @_rf_keyword("Validate Registry")
    def validate_registry(self, target_app: str, environment: str) -> None:
        """Validates app config, object registry, and definition files.

        Raises ``AssertionError`` listing every problem found so the full
        picture is visible at once rather than one error at a time.
        """
        errors: list[str] = []
        errors.extend(self._check_app_registry(target_app))
        errors.extend(self._check_dataset(target_app, environment))
        objects_by_page = self._load_object_registry(target_app, errors)
        errors.extend(self._check_cross_references(objects_by_page))
        errors.extend(self._check_definitions(target_app, environment, objects_by_page))
        _fail_if(errors)

    # ------------------------------------------------------------------
    # Internal checks
    # ------------------------------------------------------------------

    def _check_app_registry(self, target_app: str) -> list[str]:
        path = self._root / "Settings" / "AppRegistry.py"
        spec = importlib.util.spec_from_file_location("AppRegistry", path)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        try:
            mod.get_variables(target_app)
            return []
        except Exception:
            return [f"App '{target_app}' is not registered in Settings/AppRegistry.py"]

    def _check_dataset(self, target_app: str, environment: str) -> list[str]:
        errors: list[str] = []
        base = self._root / "Settings" / "DataSets" / target_app / environment
        if not base.exists():
            return [f"Dataset folder not found: Settings/DataSets/{target_app}/{environment}/"]
        for name in ("UrlRegistry.yaml", "UserRegistry.yaml", "_DatasetRegistry.robot"):
            if not (base / name).exists():
                errors.append(
                    f"Required file missing: Settings/DataSets/{target_app}/{environment}/{name}"
                )
        return errors

    def _load_object_registry(
        self, target_app: str, errors: list[str]
    ) -> dict[str, dict]:
        base = self._root / "Resources" / "PO" / "ObjectRegistry" / target_app
        if not base.exists():
            errors.append(f"ObjectRegistry not found: Resources/PO/ObjectRegistry/{target_app}/")
            return {}
        objects_by_page: dict[str, dict] = {}
        for yaml_file in sorted(base.glob("*.yaml")):
            page = yaml_file.stem
            data = _load_yaml(yaml_file)
            expected_key = f"{page}_Objects"
            if expected_key not in data:
                errors.append(
                    f"{yaml_file.name}: top-level key must be '{expected_key}'"
                )
                continue
            objects = data[expected_key] or {}
            objects_by_page[page] = objects
            errors.extend(_validate_objects(page, objects))
        return objects_by_page

    def _check_cross_references(self, objects_by_page: dict[str, dict]) -> list[str]:
        errors: list[str] = []
        for page, objects in objects_by_page.items():
            known = set(objects.keys())
            for obj_name, props in objects.items():
                strategy = (props or {}).get("LocatorStrategy", "")
                if strategy.startswith("ParentReference"):
                    parent = (props or {}).get("ParentReference")
                    if parent and parent not in known:
                        errors.append(
                            f"'{page}.yaml' → '{obj_name}': ParentReference '{parent}' "
                            f"does not exist in the same file"
                        )
                if strategy == "SelectFromGroupByCSSProperty":
                    group = (props or {}).get("GroupReference")
                    if group and group not in known:
                        errors.append(
                            f"'{page}.yaml' → '{obj_name}': GroupReference '{group}' "
                            f"does not exist in the same file"
                        )
        return errors

    def _check_definitions(
        self,
        target_app: str,
        environment: str,
        objects_by_page: dict[str, dict],
    ) -> list[str]:
        errors: list[str] = []
        base = self._root / "Settings" / "DataSets" / target_app / environment
        if not base.exists():
            return errors
        for yaml_file in sorted(base.glob("*Definitions.yaml")):
            page = yaml_file.stem.replace("Definitions", "")
            data = _load_yaml(yaml_file)
            expected_key = f"{page}_Definitions"
            if expected_key not in data:
                errors.append(
                    f"{yaml_file.name}: top-level key must be '{expected_key}'"
                )
                continue
            definitions = data[expected_key] or {}
            known_objects = set(objects_by_page.get(page, {}).keys())
            for elem, props in definitions.items():
                if known_objects and elem not in known_objects:
                    errors.append(
                        f"'{yaml_file.name}' → '{elem}': no matching object in "
                        f"ObjectRegistry/{page}.yaml"
                    )
                for prop in (props or {}):
                    if prop not in _SUPPORTED_ASSERTION_PROPS:
                        errors.append(
                            f"'{yaml_file.name}' → '{elem}': unknown assertion property "
                            f"'{prop}' — supported: {sorted(_SUPPORTED_ASSERTION_PROPS)}"
                        )
        return errors


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _validate_objects(page: str, objects: dict) -> list[str]:
    errors: list[str] = []
    for obj_name, props in objects.items():
        if not props:
            errors.append(f"'{page}.yaml' → '{obj_name}': object has no properties")
            continue
        strategy: str = props.get("LocatorStrategy", "")
        if not strategy:
            errors.append(
                f"'{page}.yaml' → '{obj_name}': missing required field 'LocatorStrategy'"
            )
            continue

        if strategy.startswith("ParentReference"):
            base = strategy[len("ParentReference"):]
            if base not in _PARENT_REF_ELIGIBLE:
                errors.append(
                    f"'{page}.yaml' → '{obj_name}': unsupported strategy '{strategy}' "
                    f"(ParentReference base must be one of: {sorted(_PARENT_REF_ELIGIBLE)})"
                )
                continue
            required = ["ParentReference"] + _BASE_STRATEGY_FIELDS[base]
        elif strategy in _BASE_STRATEGY_FIELDS:
            required = _BASE_STRATEGY_FIELDS[strategy]
        else:
            errors.append(
                f"'{page}.yaml' → '{obj_name}': unsupported LocatorStrategy '{strategy}' "
                f"— supported: {sorted(_BASE_STRATEGY_FIELDS)} or ParentReference variants"
            )
            continue

        for field in required:
            if field not in props:
                errors.append(
                    f"'{page}.yaml' → '{obj_name}': strategy '{strategy}' requires "
                    f"field '{field}'"
                )

        if props.get("UseRelation"):
            for field in ("Relation", "RelationElementType"):
                if field not in props:
                    errors.append(
                        f"'{page}.yaml' → '{obj_name}': UseRelation requires field '{field}'"
                    )
    return errors


def _load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _fail_if(errors: list[str]) -> None:
    if not errors:
        return
    bullet_list = "\n".join(f"  • {e}" for e in errors)
    raise AssertionError(
        f"Registry validation failed ({len(errors)} error(s)):\n{bullet_list}"
    )


# ---------------------------------------------------------------------------
# CLI entry point for CI validate stage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python Settings/YamlValidator.py <target_app> <environment>")
        sys.exit(1)
    target_app, environment = sys.argv[1], sys.argv[2]
    try:
        YamlValidator().validate_registry(target_app, environment)
        print(f"OK Registry validation passed for {target_app}/{environment}")
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
