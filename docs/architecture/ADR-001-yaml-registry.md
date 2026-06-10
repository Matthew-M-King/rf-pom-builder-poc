# ADR-001 — YAML Registry for Page Objects

## Context

Standard Robot Framework POM implementations hardcode locators inside keyword files.
Changing a locator requires a code change. Supporting multiple environments means conditional
variables or branching. Adding a page means writing new keyword files.

## Decision

Store locator definitions and assertion expectations in YAML files, separate from keyword logic.

| File | Purpose |
|---|---|
| `ObjectRegistry/{App}/{Page}.yaml` | Locator definitions — strategy name and required fields |
| `DataSets/{App}/{Env}/{Page}Definitions.yaml` | Assertion expectations — counts, text, images |
| `PageRegistry/_{App}Variables.robot` | Imports YAMLs as RF variable dictionaries |

The framework resolves locators at runtime by reading these dictionaries.
Switching environments changes only which YAML path is loaded, not the keyword logic.

## Benefits

- Adding a page is a YAML-only change — no keyword logic is modified.
- Environment differences are confined to YAML files; logic is environment-agnostic.
- Locators are validated before the browser starts (`YamlValidator.py`).
- YAML diffs are readable by non-developers.
- `tools/preview_locator.py` can inspect generated locators without launching a browser.

## Trade-offs

- The locator build path is not statically traceable in the same way as typed Python POM.
- IDE support for YAML key completion is limited compared to a typed model.
- Mismatched keys (definitions referencing non-existent objects) are runtime errors unless
  the validator is run — mitigated by CI running validation before every test job.

## Alternatives Considered

- **Python-based POM**: Strong typing and IDE support, but every locator change is a code change.
- **JSON registries**: Equivalent flexibility, less readable for multi-line XPath values.
- **Database-backed registry**: Maximum runtime flexibility, significant operational overhead with
  no benefit for a test automation framework targeting fixed application versions.
