*** Settings ***
Documentation       SwagLabs Website Tests

Library             Dialogs
Resource            _Resources.robot

Suite Setup         Run Keywords    Skip If    '${target_app}'!='SwagLabs'    AND    Begin Suite
Suite Teardown      Teardown Suite
Test Setup          Begin Web Test


*** Test Cases ***
Scenario: Attempt Login With Invalid Username
    [Tags]    swaglabs
    Login Validation    InvalidUser    Username and password do not match any user in this service

Scenario: Attempt Login With Invalid Password
    [Tags]    swaglabs
    Login Validation    InvalidPass    Username and password do not match any user in this service

Scenario: Attempt Login With Empty Username
    [Tags]    swaglabs
    Login Validation    EmptyUser    Username is required

Scenario: Attempt Login With Empty Password
    [Tags]    swaglabs
    Login Validation    EmptyPass    Password is required

Scenario: Attempt Login With Empty UserName and Password
    [Tags]    swaglabs
    Login Validation    EmptyAll    Username is required

Scenario: Attempt Login With Locked User
    [Tags]    swaglabs
    Login Validation    Locked    Sorry, this user has been locked out.

Scenario: Assert Login Page Elements
    [Tags]    swaglabs
    Assert Page Content    LoginPage    Default

Scenario: Assert Products Page Elements
    [Tags]    swaglabs
    Assert Page Content    ProductsPage    Default

Scenario: Assert Products Page Elements With Problem User
    [Tags]    swaglabs
    Assert Page Content    ProductsPage    Problem

Scenario: No Access To Products Page When Not Logged In
    [Tags]    swaglabs
    Given the "LoginPage" page is displayed
    When customer moves to the "ProductsPage"
    Then page should contain    You can only access '/inventory.html' when you are logged in.

Scenario: No Access To Cart Page When Not Logged In
    [Tags]    swaglabs
    Given the "LoginPage" page is displayed
    When customer moves to the "ShoppingCartPage"
    Then page should contain    You can only access '/cart.html' when you are logged in.

Scenario: Change Sort List Option to 1st option Name A to Z
    [Tags]    swaglabs
    Given the "ProductsPage" page is displayed for Default User
    When customer selects 1st "SortProducts" list option
    Then the following option should be selected in list:
    ^    Option    List
    >    NAME (A TO Z)    SortProducts
    And the "InventoryItemNames" should be sorted low to high alphabetically

Scenario: Change Sort List Option to 2nd option Name Z to A
    [Tags]    swaglabs
    Given the "ProductsPage" page is displayed for Default User
    When customer selects 2nd "SortProducts" list option
    Then the following option should be selected in list:
    ^    Option    List
    >    NAME (Z TO A)    SortProducts
    And the "InventoryItemNames" should be sorted high to low alphabetically

Scenario: Change Sort List Option to 3rd option Price High to Low
    [Tags]    swaglabs
    Given the "ProductsPage" page is displayed for Default User
    When customer selects 3rd "SortProducts" list option
    Then the following option should be selected in list:
    ^    Option    List
    >    PRICE (LOW TO HIGH)    SortProducts
    And the "InventoryItemPrices" should be sorted low to high numerical

Scenario: Change Sort List Option to last option Price High to Low
    [Tags]    swaglabs
    Given the "ProductsPage" page is displayed for Default User
    When customer selects last "SortProducts" list option
    Then the following option should be selected in list:
    ^    Option    List
    >    PRICE (HIGH TO LOW)    SortProducts
    And the "InventoryItemPrices" should be sorted high to low numerical

Scenario: Add Items to Shopping Cart
    [Tags]    swaglabs
    Given the "ProductsPage" page is displayed for Default User
    When customer adds following number of products to basket: 3
    Then the "ShoppingCart" should display text: 3

Scenario: Review Shopping Cart After Adding Items
    [Tags]    swaglabs
    Given the "ProductsPage" page is displayed for Default User
    And customer has following number of products in basket: 3
    When customer clicks the "ShoppingCartLink" link
    Then the page should display following number of "CartItems": 3
    And the shopping cart should contain correct products

Scenario: Remove Items From Shopping Cart
    [Tags]    swaglabs
    Given the "ProductsPage" page is displayed for Default User
    And customer has following number of products in basket: 3
    And customer has clicked the "ShoppingCartLink" link
    When customer removes the following amount of products from cart: 2
    Then the page should display following number of "CartItems": 1


*** Keywords ***
Login Validation
    [Arguments]    ${login_type}    ${msg}
    Given the "LoginPage" page is displayed
    When customer enters "${login_type}" login details
    Then page should contain    ${msg}

Assert Page Content
    [Arguments]    ${page}    ${login_type}
    Given the "${page}" page is displayed for ${login_type} user
    When user views elements of the current page
    Then page displays correct content
