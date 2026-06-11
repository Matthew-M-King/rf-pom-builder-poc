*** Settings ***
Library     String
Library     Browser
Resource    Page.robot


*** Keywords ***
PO: List: Select Option At Position
    [Arguments]    ${target_element}    ${position}
    ${select_locator}    Build Locator    ${target_element}
    # Browser library treats index=0 as falsy and deselects all options instead of selecting the
    # first option; select by text to avoid this — XPath option positions are 1-indexed
    IF    "${position}"=="last"
        @{options}    Get Elements    ${select_locator}//option
        ${xpath_pos}    Get Length    ${options}
    ELSE
        ${xpath_pos}    Set Variable    ${position}
    END
    ${opt_text}    Get Text    ${select_locator}//option[${xpath_pos}]
    Select Options By    ${select_locator}    text    ${opt_text}

PO: List: Assert Active Option
    [Arguments]    ${target_element}    ${value}
    ${select_locator}    Build Locator    ${target_element}
    # Pass XPath as arg to page-level JS so Playwright's locator stability check is bypassed;
    # locator.evaluate() times out if the page re-renders after selecting the already-active option
    ${actual}    Evaluate JavaScript    ${None}
    ...    xpath => { const r = document.evaluate(xpath, document, null, 9, null); const el = r.singleNodeValue; return el ? el.options[el.selectedIndex].text : ''; }
    ...    arg=${select_locator}
    ${actual_upper}    Convert To Upper Case    ${actual}
    ${expected_upper}    Convert To Upper Case    ${value}
    Should Be Equal As Strings    ${actual_upper}    ${expected_upper}
