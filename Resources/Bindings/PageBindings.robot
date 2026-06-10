*** Settings ***
Documentation       Resource file containing bindings for page related steps

Resource            ../PO/_Keywords/_AssertDefinitions.robot
Resource            ../PO/_Keywords/Input.robot
Resource            ../PO/_Keywords/List.robot
Resource            ../PO/_Keywords/Pages/LoginPagePO.robot
Library             ../Utility/TablesUtility.py


*** Keywords ***
### GIVEN ###

the "${page}" page is displayed
    PO: Page: Navigate To    ${page}

the "${page}" page is displayed for ${user_type} User
    PO: Page: Navigate To    ${page}    ${user_type}

### WHEN ###

${r:(.*)?} views elements of the current page
    ${current_page}    PO: Page: Get
    ${locators}    Build Locators
    Set Test Variable    ${${current_page}_current_page_locators}    ${locators}

${r:(.*)?} enters "${login_type}" login details
    Login App    ${login_type}

${r:(.*)?} selects ${position:(\d+|last)}${r:(st|nd|rd|th)?} "${target_list}" list option
    PO: List: Select Option At Position    ${target_list}    ${position}

${r:(.*)?} clicks the "${button}" button
    PO: Input: Await And Click Button    ${button}

${r:(.*)?} ${r:(has )?}click${r:(s|ed)?} the "${link}" link
    PO: Input: Await And Click Link    ${link}

${r:(.*)?} moves to the "${page}"
    PO: Page: Navigate To    ${page}    perform_login=${FALSE}

### THEN ###

page displays correct content
    PO: Definitions: Assert

the following option should be selected in list:
    Register Table Keyword    PO: List: Assert Active Option    Option=value    List=target_element

the "${target_elements}" should be sorted high to low ${value_type}
    PO: Page: Assert Element Group Sort Order    ${target_elements}    HighToLow${value_type}

the "${target_elements}" should be sorted low to high ${value_type}
    PO: Page: Assert Element Group Sort Order    ${target_elements}    LowToHigh${value_type}

the "${target_element}" should display text: ${text}
    PO: Page: Await And Assert Element Text    ${target_element}    ${text}

the page should display following number of "${target_element}": ${amount}
    PO: Page: Await And Assert X Number Of Elements    ${target_element}    ${amount}
