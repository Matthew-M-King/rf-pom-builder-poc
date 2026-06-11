*** Settings ***
Library     Browser
Resource    ../../Utility/ShorthandUtility.robot


*** Keywords ***
PO: Page: Get
    ${url}    Get Url
    ${is_dynamic_page}    Run Keyword And Return Status    Should Contain    ${url}    ${dynamic_url_contains}
    IF    not ${is_dynamic_page}
        FOR    ${page_name}    IN    @{UrlsToPages}
            ${expected_url}    PO: Page: Get Page Url From Registry    ${page_name}
            IF    "${expected_url}"=="${url}"
                RETURN    ${page_name}
            END
        END
    ELSE
        RETURN    ${dynamic_page_name}
    END

PO: Page: Navigate To
    [Documentation]    Navigate to ${page}, logging in as ${user} if not already authenticated.
    ...    Uses the ${current_login_user} suite-level session cache (declared in _Settings.robot)
    ...    to skip redundant logins: if the same user type is already authenticated AND the browser
    ...    is already on the target page, the keyword returns immediately. If a different user is
    ...    needed, the browser navigates to the default (login) page first. The cache is cleared
    ...    per test by Begin Web Test to prevent cross-test state leakage.
    [Arguments]    ${page}    ${user}=Default    ${perform_login}=${TRUE}
    ${actual_page}    PO: Page: Get
    ${is_page}    PO: Page: IsPage?    ${page}    ${actual_page}

    IF    "${current_login_user}"
        IF    "${current_login_user}"=="${user}"
            IF    ${is_page}
                RETURN
            END
        ELSE
            IF    "${actual_page}"!="${default_page}"
                ${page_url}    PO: Page: Get Page Url From Registry    ${default_page}
                Go To    ${page_url}
                ${actual_page}    PO: Page: Get
            END
        END
    END

    IF    "${actual_page}"=="${default_page}" and "${page}"!="${default_page}"
        IF    ${perform_login}
            ${login_url}    PO: Page: Get Page Url From Registry    ${default_page}
            Login App    ${user}
            # Login clicks the button but doesn't block until navigation completes;
            # generous timeout accommodates slow networks or sluggish test environments
            Wait Until Keyword Succeeds    30s    500ms    URL Should Not Be    ${login_url}
            Set Suite Variable    ${current_login_user}    ${user}
            ${actual_page}    PO: Page: Get
            IF    ${is_page}
                RETURN
            END
        END
        ${page_url}    PO: Page: Get Page Url From Registry    ${page}
        Go To    ${page_url}
    END

PO: Page: IsPage?
    [Arguments]    ${expected}    ${actual}
    Run Keyword And Return    Run Keyword And Return Status    Should Be Equal As Strings    ${expected}    ${actual}

PO: Page: Get Page Url From Registry
    [Arguments]    ${page}
    IF    "${UrlsToPages}[${page}]"=="BaseUrl"
        ${url}    <-    ${BaseUrl}
    ELSE
        ${url}    <-    ${BaseUrl}${UrlsToPages}[${page}]
    END
    Run Keyword And Return    <-    ${url}

URL Should Not Be
    [Arguments]    ${url}
    ${current}    Get Url
    Should Not Be Equal    ${current}    ${url}
