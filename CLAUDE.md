# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running Tests

Run all tests (default app and environment):
```
robot -d Tests/Reports .
```

Run against a specific app and environment:
```
robot -v target_app:SwagLabs -v environment:Staging -d Tests/Reports .
```

Run headless (CI mode):
```
robot -v headless:True -v target_app:SwagLabs -d Tests/Reports .
```

Run a single test by name:
```
robot -v target_app:SwagLabs -t "Scenario: Assert Login Page Elements" .
```

Run tests by tag:
```
robot -v target_app:SwagLabs -i swaglabs -d Tests/Reports .
```

Run lint (Robocop static analysis):
```
robocop .
```

PowerShell convenience script (runs both apps, respects `-Headless` flag):
```powershell
.\run_tests.ps1
.\run_tests.ps1 -Headless
```

### Default variables

Defaults come from `Settings/EnvLoader.py` (reads `.env`) and `Settings/_Settings.robot`:
- `${target_app}` = `SwagLabs`
- `${environment}` = `Staging`
- `${browser}` = `chromium`
- `${headless}` = `${FALSE}`

Copy `.env.example` to `.env` to override these locally. Browser values are mapped by `EnvLoader.py` (e.g. `chrome` → `chromium`, `edge` → `msedge`).

### First-time setup

```
pip install -r requirements.txt
rfbrowser init
```

## Architecture

Data-driven Page Object Model for Robot Framework. Locators and assertion expectations live in YAML files; `.robot` files contain no hardcoded selectors. Uses [Browser library](https://robotframework-browser.org/) (Playwright-based) instead of SeleniumLibrary.

### Core data flow

1. **EnvLoader.py** (`Settings/EnvLoader.py`) — variable provider that reads `.env` and maps raw browser names to Playwright browser IDs.

2. **AppRegistry** (`Settings/AppRegistry.py`) — variable provider (`get_variables(target_app)`) that returns app-level config (base URL, default page, dynamic URL settings).

3. **_Settings.robot** (`Settings/_Settings.robot`) — single entry point that chains all variable and resource imports for the selected app and environment. Everything else imports from here transitively.

4. **DataSets** (`Settings/DataSets/{target_app}/{environment}/`) — per-environment YAML:
   - `UrlRegistry.yaml` — maps page names to URL fragments
   - `UserRegistry.yaml` — login credentials by user type
   - `{Page}Definitions.yaml` — assertion expectations per element (count, text, image alt attributes, table content)
   - `_DatasetRegistry.robot` — imports all definition YAMLs as RF variables

5. **ObjectRegistry** (`Resources/PO/ObjectRegistry/{target_app}/{Page}.yaml`) — locator definitions per page. Each entry has a `LocatorStrategy` field and strategy-specific fields (`Xpath`, `Attribute`, `ElementType`, `Text`, etc.).

6. **PageRegistry** (`Resources/PO/PageRegistry/_{target_app}Variables.robot`) — imports ObjectRegistry YAMLs so they become `${PageName_Objects}` dictionaries. The `_${target_app}Variables.robot` naming is required — `Page.robot` resolves it dynamically.

7. **Page.robot** (`Resources/PO/_Keywords/Page.robot`) — thin facade; imports the three focused modules below. Consumers import `Page.robot` and get all keywords transitively.
   - **Navigation.robot** — `PO: Page: Navigate To`, `PO: Page: Get`, `PO: Page: Get Page Url From Registry`, `URL Should Not Be`
   - **LocatorBuilder.robot** — `Build Locator` entry point + all `Build Locator: {Strategy}` keywords; imports Navigation for `PO: Page: Get`
   - **ElementActions.robot** — `PO: Page: Get Texts`, `PO: Page: Locator Should Contain Value`, `PO: Page: Await And Assert Element Text`, etc.; imports LocatorBuilder

8. **_AssertDefinitions.robot** (`Resources/PO/_Keywords/_AssertDefinitions.robot`) — iterates `${PageName_Definitions}` and dispatches to `PO: Definitions: Assert: {PropertyKey}`. Adding a new assertion type only requires a matching keyword — no branching in the dispatcher.

9. **Bindings** (`Resources/Bindings/`) — BDD-style Given/When/Then keyword wrappers. Test cases call only bindings.

### Supported locator strategies

| Strategy | Required YAML fields |
|---|---|
| `XPathLookup` | `Xpath` |
| `WithAttribute` | `ElementType`, `Attribute`, `Name` |
| `WithText` | `ElementType`, `Text` |
| `WithContainsAttribute` | `ElementType`, `Attribute`, `Name` |
| `WithType` | `ElementType` |
| `ParentReference{Strategy}` | `ParentReference` + fields for child strategy |
| `SelectFromGroupByCSSProperty` | `GroupReference`, `CSSPropertyType`, `PropertyValue` |

All strategies optionally support `UseRelation`, `Relation`, `RelationElementType` for XPath relationship axes.

### Adding a new app

1. Add entry to `Settings/AppRegistry.py` `get_variables()`.
2. Create `Settings/DataSets/{NewApp}/{Env}/` with `UrlRegistry.yaml`, `UserRegistry.yaml`, and `_DatasetRegistry.robot`.
3. Add `{Page}Definitions.yaml` files; reference them in `_DatasetRegistry.robot`.
4. Create `Resources/PO/ObjectRegistry/{NewApp}/{Page}.yaml` for each page.
5. Create `Resources/PO/PageRegistry/_{NewApp}Variables.robot` importing those YAMLs.

### Naming conventions

- Object YAML variable blocks: `{PageName}_Objects`
- Definition YAML variable blocks: `{PageName}_Definitions`
- `_{target_app}Variables.robot` naming is required (dynamic import in `Page.robot`)
- `_`-prefixed `.robot` files are resource/setup files, not runnable suites
- PO keyword prefix: `PO: {File}: {Action}` (e.g. `PO: Page: Get`, `PO: Input: Await And Click Button`)

### ShorthandUtility operators

`Resources/Utility/ShorthandUtility.robot` defines custom RF operators used throughout:
- `<-` — alias for `Set Variable` (assignment)
- `??` — null-coalesce: returns first arg if truthy, else evaluates second arg as a keyword
- `Is Key?` — dict key existence check
- `->FOR`, `Key->`, `[_]` — iteration helpers
