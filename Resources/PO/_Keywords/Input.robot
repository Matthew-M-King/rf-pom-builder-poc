*** Settings ***
Library     String
Library     Browser
Resource    Page.robot


*** Keywords ***
PO: Input: Await And Input Text
    [Arguments]    ${target_element}    ${text}
    ${locator}    Build Locator    ${target_element}
    Fill Text    ${locator}    ${text}

PO: Input: Await And Click Button
    [Arguments]    ${target_element}
    ${locator}    Build Locator    ${target_element}
    Click    ${locator}

PO: Input: Await And Click Link
    [Arguments]    ${target_element}
    ${locator}    Build Locator    ${target_element}
    Click    ${locator}

PO: Input: Await And Click X Number Of Buttons
    [Arguments]    ${target_elements}    ${amount}
    ${locator}    Build Locator    ${target_elements}
    # Re-evaluate the locator each iteration: Get Elements returns nth-indexed locators that
    # re-resolve against current DOM, so clicking [0] each time always targets the first
    # remaining unclicked button after prior clicks change previous buttons' state
    FOR    ${_}    IN RANGE    ${amount}
        ${elements}    Get Elements    ${locator}
        Click    ${elements}[0]
    END
