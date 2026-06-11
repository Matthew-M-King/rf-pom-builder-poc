*** Settings ***
Resource    ../../Utility/ShorthandUtility.robot
Resource    Page.robot
Resource    Table.robot


*** Keywords ***
PO: Definitions: Assert
    # Property name drives keyword dispatch — adding a new assertion type only requires
    # a new "PO: Definitions: Assert: {PropertyName}" keyword, nothing here changes
    ${page}    PO: Page: Get
    ${dicts}    <-    ${${page}_Definitions}
    FOR    ${target_element}    IN    @{dicts.keys()}
        FOR    ${property}    IN    @{dicts.${target_element}.keys()}
            Run Keyword    PO: Definitions: Assert: ${property}    ${target_element}    ${dicts}
        END
    END

PO: Definitions: Assert: ShouldContain
    [Arguments]    ${target_element}    ${definitions}
    ${expected_text}    <-    ${definitions.${target_element}.ShouldContain}
    PO: Page: Locator Should Contain Value    ${target_element}    ${expected_text}

PO: Definitions: Assert: EachInGroupShouldContain
    [Arguments]    ${target_element}    ${definitions}
    @{results}    Create List
    ${text_list}    <-    ${definitions}[${target_element}][EachInGroupShouldContain]
    ${result_text}    <-    ${NONE}

    ${i}    <-    ${1}
    FOR    ${expected_text}    IN    @{text_list}
        ${locator}    Build Locator: Update Parent With Index    ${target_element}    ${i}

        ${result_locator}    ${actual_text}    Run Keyword And Ignore Error    Get Text    ${locator}

        IF    "${result_locator}"=="PASS"
            ${result_text}    ${_}    Run Keyword And Ignore Error
            ...    Should Be Equal As Strings
            ...    ${expected_text}
            ...    ${actual_text}
        END

        ${i}    Evaluate    ${i}+1
        IF    "${result_text}"=="FAIL"
            ${msg}    <-
            ...    FAIL - Expected locator ${locator} to contain text "${expected_text}" but contained "${actual_text}"
            Append To List    ${results}    ${msg}
        ELSE IF    "${result_locator}"=="FAIL"
            Append To List    ${results}    FAIL - ${actual_text}
        END
    END
    IF    not ${results}
        RETURN
    END

    FOR    ${msg}    IN    @{results}
        Log    ${msg}    WARN
    END
    Fail    Element attributes/content for locator group did not match definition

PO: Definitions: Assert: ElementCountShouldBe
    [Arguments]    ${target_element}    ${definitions}
    ${locator}    Build Locator    ${target_element}
    ${count}    <-    ${definitions}[${target_element}][ElementCountShouldBe]
    # Wait rather than assert once — gives SPAs time to finish rendering after navigation
    Wait Until Keyword Succeeds    15s    500ms    PO: Assert: Element Count    ${locator}    ${count}

PO: Assert: Element Count
    [Arguments]    ${locator}    ${count}
    @{elements}    Get Elements    ${locator}
    ${actual}    Get Length    ${elements}
    Should Be Equal As Integers    ${actual}    ${count}

PO: Definitions: Assert: TableContentShouldBe
    [Arguments]    ${target_element}    ${definitions}
    ${target_element_def}    <-    ${definitions}[${target_element}]
    ${target_content_def}    <-    ${target_element_def}[TableContentShouldBe]
    ${table_content}    <-    ${target_content_def}[Columns]
    PO: Table: Assert Table Content    ${target_element}    ${table_content}

PO: Definitions: Assert: ImageGroupAttributes
    [Arguments]    ${target_element}    ${definitions}
    ${target_element_def}    <-    ${definitions}[${target_element}]
    ${image_properties_list}    <-    ${target_element_def.ImageGroupAttributes}
    FOR    ${img_name}    IN    @{image_properties_list}
        ${properties}    <-    ${image_properties_list}[${img_name}]
        ${locator}    Build Locator: Update Parent With Index    ${target_element}    ${properties}[DefaultOrder]
        ${alt}    Get Attribute    ${locator}//img    alt
        Should Be Equal    ${alt}    ${properties}[Alt]
    END
