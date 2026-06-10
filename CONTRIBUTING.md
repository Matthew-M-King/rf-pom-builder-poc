# Contributing

## Adding a New App

Follow these five steps. Each step maps to a specific file or folder.

### 1. Register the app config

Add an entry to [Settings/AppRegistry.py](Settings/AppRegistry.py):

```python
my_app = {
    'default_page': 'HomePage',   # the page the app lands on after opening the base URL
    'dynamic_url_contains': None, # set to a URL fragment if the app has dynamic/parameterised pages
    'dynamic_page_name': None     # name used to reference dynamic pages, or None
}

def get_variables(arg):
    ...
    elif arg == 'MyApp':
        return my_app
```

### 2. Create the dataset structure

Create one folder per environment under `Settings/DataSets/MyApp/`:

```
Settings/DataSets/MyApp/
    Dev/
        _DatasetRegistry.robot
        UrlRegistry.yaml
        UserRegistry.yaml
        HomePageDefinitions.yaml   ← one per page
    Staging/
        ...
    UAT/
        ...
```

**UrlRegistry.yaml** — maps page names to URL fragments:
```yaml
BaseUrl:
  MyApp: https://my-app.example.com/
UrlsToPages:
  HomePage: BaseUrl
  LoginPage: login
  ProfilePage: user/profile
```

**UserRegistry.yaml** — login credentials per user type:
```yaml
UserLogins:
  Default:
    UserName: test_user
    Password: test_pass
```

**_DatasetRegistry.robot** — imports all definition YAML files in this environment:
```robotframework
*** Settings ***
Variables  HomePageDefinitions.yaml
```

### 3. Create the Object Registry

Add a YAML file per page under `Resources/PO/ObjectRegistry/MyApp/`. The variable block **must** be named `{PageName}_Objects`.

```yaml
# Resources/PO/ObjectRegistry/MyApp/HomePage.yaml
HomePage_Objects:
  SearchInput:
    LocatorStrategy: WithAttribute
    ElementType: input
    Attribute: placeholder
    Name: Search
  SubmitButton:
    LocatorStrategy: XPathLookup
    Xpath: //button[@type="submit"]
```

See the [locator strategy table in the README](README.md#locator-strategies) for all supported strategies and their required fields.

### 4. Create the Page Registry file

Add `Resources/PO/PageRegistry/_MyAppVariables.robot`. The filename convention is required — `LocatorBuilder.robot` resolves it as `_${target_app}Variables.robot` at runtime.

```robotframework
*** Settings ***
Variables  ../ObjectRegistry/${target_app}/HomePage.yaml
```

Add one `Variables` line per page YAML file.

### 5. Create Definition files

For each page, add a `{Page}Definitions.yaml` in each environment dataset folder. The variable block **must** be named `{PageName}_Definitions`, and element keys must match the corresponding `_Objects` keys exactly.

```yaml
# Settings/DataSets/MyApp/Staging/HomePageDefinitions.yaml
HomePage_Definitions:
  SearchInput:
    ElementCountShouldBe: 1
  SubmitButton:
    ElementCountShouldBe: 1
```

Then reference it in `_DatasetRegistry.robot`:
```robotframework
*** Settings ***
Variables  HomePageDefinitions.yaml
```

---

## Adding a New Page to an Existing App

1. Add `{Page}.yaml` to `Resources/PO/ObjectRegistry/{App}/`
2. Add a `Variables` line to `Resources/PO/PageRegistry/_{App}Variables.robot`
3. Add `{Page}Definitions.yaml` to each environment folder under `Settings/DataSets/{App}/`
4. Reference the new definitions file in each environment's `_DatasetRegistry.robot`
5. Add a URL entry for the page in each environment's `UrlRegistry.yaml`

---

## Local Setup

```bash
pip install -r requirements.txt
rfbrowser init          # downloads Playwright browser binaries (one-time, ~300 MB)
```

Run all apps:
```powershell
.\run_tests.ps1              # headed
.\run_tests.ps1 -Headless    # headless
```

---

## Linting

This project uses [Robocop](https://robocop.readthedocs.io/) for static analysis. Run it before submitting a pull request:

```bash
robocop .
```

Configuration is in [pyproject.toml](pyproject.toml) under `[tool.robocop]`.
