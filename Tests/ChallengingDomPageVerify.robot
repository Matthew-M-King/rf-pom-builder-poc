*** Settings ***
Documentation  Challenging DOM Page Verify

Resource        _Resources.robot
Suite Setup     Run Keywords    Skip If    '${target_app}'!='ChallengingDom'    AND    Begin Suite
Suite Teardown  Teardown Suite

*** Test Cases ***
Scenario: Assert Challenging DOM Elements
    [Tags]  ChallengingDom
    Given the "MainPage" page is displayed
     When user views elements of the current page
     Then page displays correct content