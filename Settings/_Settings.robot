*** Settings ***
Variables       EnvLoader.py
Variables       AppRegistry.py    ${target_app}
Resource        DataSets/${target_app}/${environment}/_DatasetRegistry.robot
Resource        ../Resources/PO/PageRegistry/_${target_app}Variables.robot


*** Variables ***
# Suite-level session cache. PO: Page: Navigate To skips re-login when the same user type is
# already authenticated. Reset to empty by Begin Web Test to enforce per-test isolation.
${current_login_user}
# Set to ${TRUE} (or pass -v debug_locator_build:True) to log every locator build at WARN level.
${debug_locator_build}    ${FALSE}
