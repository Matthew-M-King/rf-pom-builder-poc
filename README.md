# Robot Framework POM Builder POC

[![Tests](https://github.com/Matthew-M-King/rf-pom-builder-poc/actions/workflows/tests.yml/badge.svg)](https://github.com/Matthew-M-King/rf-pom-builder-poc/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/github/license/Matthew-M-King/rf-pom-builder-poc)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/Matthew-M-King/rf-pom-builder-poc)](https://github.com/Matthew-M-King/rf-pom-builder-poc/commits/main)
[![Linting: Robocop](https://img.shields.io/badge/linting-robocop-brightgreen)](https://robocop.readthedocs.io)

A data-driven Page Object Model framework for Robot Framework where locators and element definitions live in **YAML files**, not in `.robot` code. Adding a page, swapping an environment, or changing a locator strategy requires no changes to keyword logic.

## Table of Contents

- [Why This Exists](#why-this-exists)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Running Tests](#running-tests)
- [Core Registry Structure](#core-registry-structure)
- [Register an App](#register-an-app)
- [Register Urls](#register-urls)
- [Register Users](#register-users)
- [Register Pages](#register-pages)
- [Object Registry](#object-registry)
- [Definition Registry](#definition-registry)
- [Adding a New Page — Worked Example](#adding-a-new-page--worked-example)

---

## Why This Exists

Standard Robot Framework POM implementations hardcode locators inside `.robot` keyword files. This means a locator change requires a code change, locators for different environments must be branched or conditionally set, and adding a new page requires creating new keyword files.

This framework separates **what to find** (YAML) from **how to find it** (keyword logic):

| Concern | Where it lives |
|---|---|
| Locator strategies & XPath construction | `LocatorBuilder.robot` (written once) |
| Locator definitions per page | `ObjectRegistry/{App}/{Page}.yaml` |
| Assertion rules per page | `DataSets/{App}/{Env}/{Page}Definitions.yaml` |
| URL and user data per environment | `DataSets/{App}/{Env}/UrlRegistry.yaml` etc. |

The result: adding a new page is a YAML-only change. Swapping environments passes a single CLI variable.

**Trade-off**: The dynamic dispatch in `LocatorBuilder.robot` (using `Run Keyword` to call strategy-named keywords) makes the locator-build path less statically traceable than hardcoded POM files. This is a deliberate choice — the extensibility gain outweighs the traceability cost for teams adding pages frequently.

---

## Architecture

```
Tests/*.robot
    │
    └─► Bindings (Given/When/Then wrappers)
            │
            └─► Page.robot  ← thin facade; consumers import this one file
                    │
          ┌─────────┼──────────────────┐
          ▼         ▼                  ▼
  Navigation   LocatorBuilder    ElementActions
  .robot       .robot            .robot
  (URL ↔       (Build Locator    (Get Texts,
  page name)   dispatches to     Assert Count,
               Build Locator:    Sort Order)
               {Strategy})
                    │
          ┌─────────┴──────────────┐
          ▼                        ▼
  ObjectRegistry YAMLs       DataSets YAMLs
  (locator definitions)      (URLs, users, element definitions)
  Resources/PO/              Settings/DataSets/
  ObjectRegistry/            {target_app}/{environment}/
  {target_app}/{Page}.yaml
```

### Key files

| File | Role |
|---|---|
| [Settings/AppRegistry.py](Settings/AppRegistry.py) | RF variable provider — returns app config dict for `${target_app}` |
| [Settings/YamlValidator.py](Settings/YamlValidator.py) | Validates all YAML registries before the browser starts; also a CLI tool for CI |
| [Settings/_Settings.robot](Settings/_Settings.robot) | Imports AppRegistry and the active DataSet; defines default CLI variables |
| [Resources/PO/_Keywords/Page.robot](Resources/PO/_Keywords/Page.robot) | Thin facade — consumers import this one file and get everything transitively |
| [Resources/PO/_Keywords/Navigation.robot](Resources/PO/_Keywords/Navigation.robot) | `PO: Page: Navigate To`, `PO: Page: Get` (URL → page name) |
| [Resources/PO/_Keywords/LocatorBuilder.robot](Resources/PO/_Keywords/LocatorBuilder.robot) | All `Build Locator: {Strategy}` keywords; dispatches via `Run Keyword` |
| [Resources/PO/_Keywords/ElementActions.robot](Resources/PO/_Keywords/ElementActions.robot) | Element text retrieval, count and sort assertions |
| [Resources/PO/_Keywords/_AssertDefinitions.robot](Resources/PO/_Keywords/_AssertDefinitions.robot) | Iterates `${PageName_Definitions}` and dispatches assertion keywords |
| [Resources/Bindings/PageBindings.robot](Resources/Bindings/PageBindings.robot) | BDD-style Given/When/Then bindings consumed by test cases |

---

## Quick Start

**Prerequisites:** Python 3.9+

```bash
pip install -r requirements.txt
rfbrowser init
```

> Tests run against live demo sites ([saucedemo.com](https://www.saucedemo.com) and [the-internet.herokuapp.com](https://the-internet.herokuapp.com)). An internet connection is required.

---

## Running Tests

Each app must be run with its own `target_app` variable — the settings (URL registry, page objects, definitions) are all app-scoped and loaded at suite initialisation time, so mixing two apps in one `robot .` command is not supported.

Run all apps (uses `run_tests.ps1`):
```powershell
.\run_tests.ps1              # headed
.\run_tests.ps1 -Headless    # headless
```

Run a single app directly:
```bash
robot -v target_app:SwagLabs -i swaglabs -d Tests/Reports .
robot -v target_app:ChallengingDom -i ChallengingDom -d Tests/Reports .
```

Override environment:
```bash
robot -v target_app:SwagLabs -v environment:Dev -i swaglabs -d Tests/Reports .
```

Run a single test by name:
```bash
robot -v target_app:SwagLabs -t "Scenario: Assert Login Page Elements" .
```

**Available variables**

| Variable | Default | Options |
|---|---|---|
| `target_app` | `SwagLabs` | `SwagLabs`, `ChallengingDom` |
| `environment` | `Staging` | `Dev`, `Staging`, `UAT` |
| `browser` | `chromium` | `chromium`, `firefox`, `webkit`, `msedge` |
| `headless` | `${FALSE}` | `True`, `False` |

---

## Core Registry Structure

```
└───Settings
│   │  _Settings.robot
│   │  AppRegistry.py
│   │
│   └───DataSets
│   │  │
│   │  └───ChallengingDom
│   │  │   └───Dev / Staging / UAT
│   │  │       _DatasetRegistry.robot
│   │  │       MainPageDefinitions.yaml
│   │  │       UrlRegistry.yaml
│   │  │       UserRegistry.yaml
│   │  │
│   │  └───SwagLabs
│   │      └───Dev / Staging / UAT
│   │          _DatasetRegistry.robot
│   │          LoginPageDefinitions.yaml
│   │          ProductsPageDefinitions.yaml
│   │          ShoppingCartPageDefinitions.yaml
│   │          UrlRegistry.yaml
│   │          UserRegistry.yaml
│
└───Resources
    └───PO
        ├───ObjectRegistry
        │   ├───ChallengingDom
        │   │   MainPage.yaml
        │   └───SwagLabs
        │       LoginPage.yaml
        │       ProductsPage.yaml
        │       ShoppingCartPage.yaml
        │
        └───PageRegistry
            _ChallengingDomVariables.robot
            _SwagLabsVariables.robot
```

---

## Register an App

`Settings/AppRegistry.py`

Add a new entry in `get_variables()` keyed by the app name you'll pass as `${target_app}`:

```python
app3 = {
    'default_page': 'MainPage',       # landing page name (must match UrlsToPages key)
    'dynamic_url_contains': None,     # partial URL fragment for dynamic pages, or None
    'dynamic_page_name': None         # name for dynamic pages, or None
}

def get_variables(arg):
    if arg == 'ExampleApp':
        return app3
```

---

## Register Urls

`Settings/DataSets/{target_app}/{environment}/UrlRegistry.yaml`

```yaml
BaseUrl:
  ExampleApp: https://www.example_app.com/
UrlsToPages:
  MainPage: BaseUrl          # resolves to BaseUrl directly
  ExamplePage: example_page  # resolves to BaseUrl + fragment
```

---

## Register Users

`Settings/DataSets/{target_app}/{environment}/UserRegistry.yaml`

```yaml
UserLogins:
  Default:
    UserName: standard_user
    Password: secret_sauce
  Locked:
    UserName: locked_out_user
    Password: secret_sauce
```

---

## Register Pages

`Resources/PO/PageRegistry/_{target_app}Variables.robot`

Create a file named `_{YourApp}Variables.robot` — the name is resolved dynamically by `LocatorBuilder.robot`. It only needs `Variables` imports pointing to the ObjectRegistry YAMLs:

```robotframework
*** Settings ***
Variables  ../ObjectRegistry/${target_app}/ExamplePage.yaml
```

---

## Object Registry

`Resources/PO/ObjectRegistry/{target_app}/{Page}.yaml`

Each YAML file represents one page. The variable block must be named `{PageName}_Objects`.

```yaml
LoginPage_Objects:
  Username:
    LocatorStrategy: XPathLookup
    Xpath: //input[@data-test="username"]
  Password:
    LocatorStrategy: WithAttribute
    ElementType: input
    Attribute: data-test
    Name: password
```

### Locator strategies

| Strategy | Required fields | Description |
|---|---|---|
| `XPathLookup` | `Xpath` | Direct XPath expression |
| `WithAttribute` | `ElementType`, `Attribute`, `Name` | `//type[@attr="name"]` |
| `WithText` | `ElementType`, `Text` | `//type[normalize-space()="text"]` |
| `WithContainsAttribute` | `ElementType`, `Attribute`, `Name` | `//type[contains(@attr, "name")]` |
| `ParentReferenceWithXpathLookup` | `ParentReference` + XPathLookup fields | Parent locator prefixed to child XPath |
| `ParentReferenceWithAttribute` | `ParentReference` + WithAttribute fields | Parent locator prefixed to child attribute locator |
| `ParentReferenceWithText` | `ParentReference` + WithText fields | Parent locator prefixed to child text locator |
| `ParentReferenceWithContainsAttribute` | `ParentReference` + WithContainsAttribute fields | Parent locator prefixed to contains-attribute locator |
| `ParentReferenceWithType` | `ParentReference`, `ElementType` | Parent locator prefixed to `//type` |
| `SelectFromGroupByCSSProperty` | `GroupReference`, `CSSPropertyType`, `PropertyValue` | Iterates a group of elements and returns the one matching a CSS property value |

---

## Definition Registry

`Settings/DataSets/{target_app}/{environment}/{Page}Definitions.yaml`

Definition files describe what to assert on each page. The variable block must be named `{PageName}_Definitions`, and element keys must match the corresponding `{PageName}_Objects` keys.

```yaml
LoginPage_Definitions:
  Username:
    ElementCountShouldBe: 1
  LoginCredentials:
    ElementCountShouldBe: 1
    ShouldContain:
      - standard_user
      - locked_out_user
```

Import each definition file in `Settings/DataSets/{target_app}/{environment}/_DatasetRegistry.robot`:

```robotframework
*** Settings ***
Variables  LoginPageDefinitions.yaml
Variables  ProductsPageDefinitions.yaml
```

### Supported assertion properties

| Property | Description |
|---|---|
| `ElementCountShouldBe` | Asserts the element appears exactly N times on the page |
| `ShouldContain` | Asserts the element's text contains all listed strings |
| `EachInGroupShouldContain` | For a parent-reference group: asserts each indexed child contains the expected text |
| `TableContentShouldBe` | Asserts table column content matches a defined structure |
| `ImageGroupAttributes` | Asserts `alt` and `src` attributes for a group of images |

---

## Adding a New Page — Worked Example

This walkthrough adds a `CheckoutPage` to the SwagLabs app. Every step is a file you create or extend — no changes to keyword logic required.

### 1. Add the URL

`Settings/DataSets/SwagLabs/{Env}/UrlRegistry.yaml` — repeat for Dev, Staging, UAT:

```yaml
UrlsToPages:
  CheckoutPage: checkout-step-one   # appended to BaseUrl
```

### 2. Add the Object Registry

`Resources/PO/ObjectRegistry/SwagLabs/CheckoutPage.yaml`

The variable block name **must** be `CheckoutPage_Objects`:

```yaml
CheckoutPage_Objects:
  FirstNameInput:
    LocatorStrategy: WithAttribute
    ElementType: input
    Attribute: data-test
    Name: firstName

  LastNameInput:
    LocatorStrategy: WithAttribute
    ElementType: input
    Attribute: data-test
    Name: lastName

  ContinueButton:
    LocatorStrategy: XPathLookup
    Xpath: //input[@data-test="continue"]

  FormErrorMessage:
    LocatorStrategy: WithContainsAttribute
    ElementType: h3
    Attribute: data-test
    Name: error
```

### 3. Register it in the Page Registry

`Resources/PO/PageRegistry/_SwagLabsVariables.robot` — add one line:

```robotframework
*** Settings ***
Variables  ../ObjectRegistry/${target_app}/CheckoutPage.yaml
```

### 4. Add the Definition file

`Settings/DataSets/SwagLabs/{Env}/CheckoutPageDefinitions.yaml` — repeat for Dev, Staging, UAT.

Element keys must match `CheckoutPage_Objects` exactly:

```yaml
CheckoutPage_Definitions:
  FirstNameInput:
    ElementCountShouldBe: 1
  LastNameInput:
    ElementCountShouldBe: 1
  ContinueButton:
    ElementCountShouldBe: 1
```

### 5. Import the Definition file

`Settings/DataSets/SwagLabs/{Env}/_DatasetRegistry.robot` — add one line:

```robotframework
*** Settings ***
Variables  CheckoutPageDefinitions.yaml
```

### Verify

Preview any locator without running the browser:

```bash
python tools/preview_locator.py SwagLabs CheckoutPage ContinueButton
# [CheckoutPage → ContinueButton]
# Strategy : XPathLookup
# Locator  : //input[@data-test="continue"]
```

Run the YAML validator to catch typos before launching the suite:

```bash
python Settings/YamlValidator.py SwagLabs Staging
# OK Registry validation passed for SwagLabs/Staging
```
