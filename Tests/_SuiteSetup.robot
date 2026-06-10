*** Settings ***
Documentation       Setup Tests

Library             Browser
Library             ../Settings/YamlValidator.py
Resource            ../Settings/_Settings.robot
Resource            ../Resources/Utility/ShorthandUtility.robot
Library             ../Resources/Utility/TablesUtility.py
Resource            ../Resources/PO/_Keywords/Pages/LoginPagePO.robot


*** Keywords ***
Begin Suite
    Validate Registry    ${target_app}    ${environment}
    New Browser    ${browser}    headless=${headless}
    New Context
    New Page    ${BaseUrl}
    Set Viewport Size    1920    1080

Begin Suite With ${user_type} User
    Begin Suite
    Login App    ${user_type}

Begin Web Test
    Set Suite Variable    ${current_login_user}    ${EMPTY}
    Delete All Cookies
    Delete Storage
    Go To    ${BaseUrl}

Teardown Suite
    Run Keyword And Ignore Error    Close Browser

Delete Storage
    [Documentation]    Clears localStorage and sessionStorage; call before Reload to ensure a clean test state.
    Evaluate JavaScript    ${None}    () => { window.localStorage.clear(); window.sessionStorage.clear(); }

page should contain
    [Arguments]    ${text}
    ${body}    Get Text    body
    Should Contain    ${body}    ${text}
