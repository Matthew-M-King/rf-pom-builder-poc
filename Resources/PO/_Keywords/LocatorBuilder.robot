*** Settings ***
Library     Browser
Library     Collections
Library     String
Resource    ../../Utility/ShorthandUtility.robot
Resource    Navigation.robot
Resource    CustomStrategies.robot


*** Keywords ***
Build Locator
    [Documentation]    Build locator based on locator definition yaml files and supported locator strategies:
    ...    XPathLookup, WithAttribute, WithText, WithContainsAttribute, WithType,
    ...    SelectFromGroupByCSSProperty,
    ...    ParentReference{Strategy} — where {Strategy} is any of the above except SelectFromGroupByCSSProperty.
    ...    All strategies optionally support UseRelation/Relation/RelationElementType for XPath axes.
    [Arguments]    ${target_element}    ${extension}=${EMPTY}    ${page}=${NONE}

    # page can be injected for parent-reference recursion; otherwise derive it from the current URL
    ${page}    ??    ${page}    PO: Page: Get
    TRY
        ${properties}    <-    ${${page}_Objects.${target_element}}
    EXCEPT    AS    ${err}
        Fail
        ...    Object '${target_element}' not found on page '${page}' — check ObjectRegistry/${page}.yaml
    END

    ${strategy}    <-    ${properties.LocatorStrategy}
    IF    $strategy.startswith('ParentReference')
        ${locator_strategy}    <-    ParentReference
    ELSE
        ${locator_strategy}    <-    ${strategy}
    END

    # Strategy dispatch — any "Build Locator: {StrategyName}" keyword in scope is automatically
    # available. Built-in strategies live in this file; custom ones go in CustomStrategies.robot.
    TRY
        ${locator}    Run Keyword    Build Locator: ${locator_strategy}    ${properties}    ${page}    ${extension}
    EXCEPT    No keyword with name*    type=glob
        Fail
        ...    Unknown LocatorStrategy '${locator_strategy}' for '${target_element}' on page '${page}'.
        ...    Add 'Build Locator: ${locator_strategy}' to CustomStrategies.robot or fix ObjectRegistry/${page}.yaml.
    END
    IF    ${debug_locator_build}
        Log
        ...    [Locator Build] app=${target_app} page=${page} element=${target_element} strategy=${locator_strategy}\n  ${locator}
        ...    WARN
    END
    [Return]    ${locator}

Build Locator: ParentReference
    # Strips "ParentReference" prefix from the strategy name, resolves the parent element
    # recursively, then prepends it — allowing arbitrarily deep parent chains
    [Arguments]    ${properties}    ${page}    ${extension}=${EMPTY}
    ${child_locator_strategy}    Remove String    ${properties.LocatorStrategy}    ParentReference
    ${parent_reference}    <-    ${properties.ParentReference}
    ${parent_locator}    Build Locator    ${parent_reference}    page=${page}
    ${locator}    Run Keyword    Build Locator: ${child_locator_strategy}    ${properties}    ${page}    ${extension}
    Run Keyword And Return    <-    ${parent_locator}${locator}

Build Locator: XPathLookup
    [Arguments]    ${properties}    ${page}    ${extension}=${EMPTY}
    ${axes}    Build Locator: Add Relationship Axes    ${properties}    ${page}    ${extension}
    Run Keyword And Return    <-    ${axes}${properties.Xpath}

Build Locator: WithType
    [Arguments]    ${properties}    ${page}    ${extension}=${EMPTY}
    ${type}    <-    ${properties.ElementType}
    ${axes}    Build Locator: Add Relationship Axes    ${properties}    ${page}    ${extension}=${EMPTY}
    Run Keyword And Return    <-    ${axes}//${type}

Build Locator: WithAttribute
    [Arguments]    ${properties}    ${page}    ${extension}=${EMPTY}
    ${attribute}    <-    ${properties.Attribute}
    ${name}    <-    ${properties.Name}
    ${type}    <-    ${properties.ElementType}
    ${axes}    Build Locator: Add Relationship Axes    ${properties}    ${page}    ${extension}=${EMPTY}
    Run Keyword And Return    <-    ${axes}//${type}\[@${attribute}="${name}"]${extension}

Build Locator: WithText
    [Arguments]    ${properties}    ${page}    ${extension}=${EMPTY}
    ${text}    <-    ${properties.Text}
    ${type}    <-    ${properties.ElementType}
    ${axes}    Build Locator: Add Relationship Axes    ${properties}    ${page}    ${extension}=${EMPTY}
    Run Keyword And Return    <-    ${axes}//${type}\[normalize-space()="${text}"]${extension}

Build Locator: WithContainsAttribute
    [Arguments]    ${properties}    ${page}    ${extension}=${EMPTY}
    ${attribute}    <-    ${properties.Attribute}
    ${name}    <-    ${properties.Name}
    ${axes}    Build Locator: Add Relationship Axes    ${properties}    ${page}    ${extension}=${EMPTY}
    Run Keyword And Return
    ...    <-
    ...    ${axes}//${properties.ElementType}\[contains(@${attribute}, "${name}")]${extension}

Build Locator: SelectFromGroupByCSSProperty
    [Arguments]    ${properties}    ${page}    ${extension}=${EMPTY}
    ${group_reference}    <-    ${properties.GroupReference}
    ${css_property_type}    <-    ${properties.CSSPropertyType}
    ${group_locator}    Build Locator    ${group_reference}    page=${page}
    @{group}    Get Elements    ${group_locator}
    FOR    ${element}    IN    @{group}
        ${element_property}    Evaluate JavaScript    ${element}
        ...    e => window.getComputedStyle(e).getPropertyValue('${css_property_type}')
        Return From Keyword If    "${element_property}"=="${properties.PropertyValue}"    ${element}
    END

Build Locator: Add Relationship Axes
    [Arguments]    ${properties}    ${page}    ${extension}=${EMPTY}
    ${is_relation}    Is Key?    ${properties}    UseRelation
    Return From Keyword If    not ${is_relation}    ${EMPTY}
    Return From Keyword If    not ${properties.UseRelation}    ${EMPTY}
    ${relation}    <-    ${properties.Relation}
    ${type}    <-    ${properties.RelationElementType}
    Run Keyword And Return    <-    //${relation}::${type}

### INTERNAL ###

Build Locators
    @{locators}    Create List
    ${page}    PO: Page: Get
    ${dicts}    <-    ${${page}_Objects}
    FOR    ${target_element}    IN    @{dicts.keys()}
        &{locator_details}    Create Dictionary
        ${locator}    Build Locator    ${target_element}
        Set To Dictionary
        ...    ${locator_details}
        ...    Name=${target_element}
        ...    Locator=${locator}
        ...    ${target_element}=${locator}
        Append To List    ${locators}    ${locator_details}
    END
    [Return]    ${locators}

Build Locator: Get Parent Target Element
    [Arguments]    ${target_element}
    ${page}    PO: Page: Get
    ${dicts}    <-    ${${page}_Objects}
    Run Keyword And Return    <-    ${dicts.${target_element}.ParentReference}

Build Locator: Update Parent With Index
    [Arguments]    ${target_element}    ${index}
    ${target_parent_element}    Build Locator: Get Parent Target Element    ${target_element}
    ${parent_locator}    Build Locator    ${target_parent_element}
    ${locator}    Build Locator    ${target_element}
    ${locator}    Replace String    ${locator}    ${parent_locator}    ${EMPTY}

    ${parent_locator}    <-    ${parent_locator}\[${index}]
    Run Keyword And Return    <-    ${parent_locator}${locator}
