# ADR-003 — YAML Validation Before Browser Launch

## Context

YAML-defined locators introduce failure modes that typed code prevents at compile time:
missing required fields, unknown strategy names, broken cross-references between objects,
and definition keys that don't match their ObjectRegistry counterpart. Without an early
validation step these produce cryptic mid-test failures long after the browser has launched.

## Decision

`YamlValidator.py` runs as the first action in `Begin Suite`, before the browser opens.
It validates:

- App registration in `AppRegistry.py`
- Dataset folder structure and required files per environment
- ObjectRegistry YAML structure: `LocatorStrategy` present, required fields for each strategy
- Prefix detection for `ParentReference` strategies; cross-reference integrity within the page
- `UseRelation: true` implies both `Relation` and `RelationElementType` are present
- Definition file element keys correspond to entries in the matching ObjectRegistry

`YamlValidator.py` also runs as a standalone CLI, used by the CI `validate` stage before
Playwright browsers are installed — providing fast feedback without the ~2-minute browser setup:

```bash
python Settings/YamlValidator.py SwagLabs Staging
```

CI validates all app × environment combinations (currently 6 jobs) so Dev and UAT YAML
breakage is caught before it reaches the `test` stage.

## Benefits

- Broken YAML fails in under one second with a complete, structured error list rather than a
  cryptic locator error mid-run.
- CI catches YAML errors in the `validate` stage before spending time on browser installation.
- All environments are validated in CI regardless of which environment runs the tests.
- The validator and the runtime share the same strategy/assertion constant tables, so they
  stay in sync automatically.

## Trade-offs

- Adds approximately 100ms to suite startup (negligible in practice).
- `YamlValidator` must be updated when new strategies or assertion properties are added.
  If `CustomStrategies.robot` adds a strategy, `_BASE_STRATEGY_FIELDS` should be extended.
- Cross-page cross-references (e.g., `GroupReference` pointing to a different page's object)
  are not validated — objects are loaded per-page.

## Alternatives Considered

- **Validate on first use**: Catch errors when `Build Locator` is called. Simpler, but errors
  surface deep in a test run rather than at startup, making triage slower.
- **JSON Schema / Pydantic models**: More rigorous structural validation. Adds a schema file
  to maintain and does not naturally capture cross-reference relationships between files.
- **No validation**: Acceptable for simple projects; not appropriate once the registry grows
  beyond a handful of pages or is maintained by multiple people.
