*** Settings ***
Resource    Page.robot


*** Variables ***
${locator_table_cell}       //tbody/tr[{0}]//td[{1}]


*** Keywords ***
PO: Table: Assert Table Content
    [Arguments]    ${target_element}    ${expected_table_content}
    ${table_locator}    Build Locator    ${target_element}
    @{results}    Create List

    FOR    ${col}    IN    @{expected_table_content}
        ${rows}    <-    ${expected_table_content.${col}.Rows}
        ${col_index}    <-    ${expected_table_content.${col}.ColumnNo}
        ${row_index}    <-    ${1}

        FOR    ${expected_table_cell_value}    IN    @{rows}
            ${text_result}    Create List    PASS    ${EMPTY}
            ${current_cell}    Format String    ${locator_table_cell}    ${row_index}    ${col_index}
            ${current_table_cell}    <-    ${table_locator}${current_cell}
            ${locator_result}    Run Keyword And Ignore Error    Get Text    ${current_table_cell}

            IF    "${locator_result}[0]"=="PASS"
                ${text_result}    Run Keyword And Ignore Error
                ...    Should Be Equal As Strings
                ...    ${expected_table_cell_value}
                ...    ${locator_result}[1]
            END

            IF    "${text_result[0]}" == "FAIL"
                Append To List
                ...    ${results}
                ...    Fail -- the text "${expected_table_cell_value}" wasn't found in following cell: ${current_table_cell}
            ELSE IF    "${locator_result}[0]"=="FAIL"
                Append To List
                ...    ${results}
                ...    Fail -- the following table cell locator wasn't found: ${current_table_cell}
            END

            ${row_index}    Evaluate    ${row_index}+1
        END
    END

    IF    not ${results}
        RETURN
    END

    FOR    ${msg}    IN    @{results}
        Log    ${msg}    WARN
    END
    Fail    Table content or table definition was incorrect
