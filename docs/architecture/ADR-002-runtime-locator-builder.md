# ADR-002 — Runtime Locator Builder with Named-Keyword Dispatch

## Context

Once locators live in YAML, the framework needs a mechanism to translate strategy names and
field dictionaries into Browser library locator strings at runtime. The mechanism must be
extensible without requiring changes to a central dispatcher.

## Decision

Use Robot Framework's `Run Keyword` with a naming convention to dispatch strategy implementations:

```robot
Run Keyword    Build Locator: ${locator_strategy}    ${properties}    ${page}    ${extension}
```

Each strategy is a Robot Framework keyword named `Build Locator: {StrategyName}`.
The keyword name IS the registration — no registry file to maintain.

Built-in strategies live in `LocatorBuilder.robot`.
Custom strategies belong in `CustomStrategies.robot`, which is imported by `LocatorBuilder.robot`.
Adding a strategy requires one keyword implementation; the dispatcher never changes.

An unknown strategy name produces a targeted error:
> Unknown LocatorStrategy 'X' for 'Y' on page 'Z' — add 'Build Locator: X' to CustomStrategies.robot

## Benefits

- Open/closed: open for extension (new keyword), closed for modification (dispatcher unchanged).
- No registry file to keep in sync with implementations.
- `YamlValidator.py` validates strategy names against the known set before execution, so
  unknown strategies are caught before the browser launches.
- Custom strategies are first-class — no special API, just a keyword with a matching name.

## Trade-offs

- `Run Keyword` calls are not directly navigable in most IDEs.
- Strategy existence is not validated at load time for strategies in `CustomStrategies.robot`
  (only built-in strategies are in `YamlValidator._BASE_STRATEGY_FIELDS`). Custom strategies
  registered in `CustomStrategies.robot` should also be added to `_BASE_STRATEGY_FIELDS`.
- All strategy keywords must conform to the `(properties, page, extension)` signature
  convention — this is implicit, not enforced by a type system.

## Alternatives Considered

- **Dictionary-based registry**: `${STRATEGIES}[${strategy}]` → keyword name. More explicit
  but requires maintaining a registry dict in sync with implementations — two places to edit.
- **Python dispatch table in a library**: Fully typed, IDE-navigable. Forces locator logic into
  Python, losing the composability and readability of Robot Framework keyword implementations.
- **IF/ELSE chain**: Requires modifying the dispatcher for every new strategy. Rejected.
