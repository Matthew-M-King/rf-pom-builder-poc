*** Settings ***
Library     Collections
Library     String
Library     Browser
Resource    LocatorBuilder.robot


*** Keywords ***
PO: Page: Get Texts
    [Documentation]    Get list of text from multiple web elements
    [Arguments]    ${target_element}
    ${locator}    Build Locator    ${target_element}
    @{elements}    Get Elements    ${locator}
    @{element_text_list}    Create List
    FOR    ${element}    IN    @{elements}
        ${element_text}    Get Text    ${element}
        Append To List    ${element_text_list}    ${element_text}
    END
    RETURN    ${element_text_list}

PO: Page: Locator Should Contain Value
    [Arguments]    ${target_element}    ${expected_text}
    ${locator}    Build Locator    ${target_element}
    ${actual_text}    Get Text    ${locator}
    FOR    ${text}    IN    @{expected_text}
        Should Contain    ${actual_text}    ${text}
    END

PO: Page: Await And Assert Element Text
    [Arguments]    ${target_element}    ${text}
    ${locator}    Build Locator    ${target_element}
    ${actual}    Get Text    ${locator}
    Should Be Equal As Strings    ${actual}    ${text}

PO: Page: Await And Assert X Number Of Elements
    [Arguments]    ${target_element}    ${count}
    ${locator}    Build Locator    ${target_element}
    @{elements}    Get Elements    ${locator}
    ${actual}    Get Length    ${elements}
    Should Be Equal As Integers    ${actual}    ${count}

PO: Page: Assert Element Group Sort Order
    [Arguments]    ${target_elements}    ${order}
    ${order}    Convert To Lower Case    ${order}

    ${texts}    PO: Page: Get Texts    ${target_elements}
    Should Not Be Empty    ${texts}    No elements found for sort assertion on '${target_elements}'
    @{actual_list}    Create List

    IF    "numerical" in "${order}"
        FOR    ${text}    IN    @{texts}
            ${matches}    Get Regexp Matches    ${text}    \\d+
            IF    ${matches}
                ${values}    <-    ${EMPTY}
                FOR    ${value}    IN    @{matches}
                    ${values}    Catenate    ${values}${value}
                END
                ${values}    Convert To Integer    ${values}
            END
            Append To List    ${actual_list}    ${values}
        END
        ${expected_list}    Copy List    ${actual_list}
        Sort List    ${expected_list}

        IF    "hightolow" in "${order}"
            Reverse List    ${expected_list}
            Lists Should Be Equal    ${actual_list}    ${expected_list}
        ELSE
            Lists Should Be Equal    ${actual_list}    ${expected_list}
        END

    ELSE
        ${actual_list}    <-    ${texts}
        ${expected_list}    Copy List    ${actual_list}

        Sort List    ${expected_list}

        IF    "hightolow" in "${order}"
            Reverse List    ${expected_list}
            Lists Should Be Equal    ${actual_list}    ${expected_list}
        ELSE
            Lists Should Be Equal    ${actual_list}    ${expected_list}
        END

    END
