*** Settings ***
Documentation
...    Extension point for custom locator strategies.
...
...    Any keyword named "Build Locator: {StrategyName}" defined here is automatically
...    available to the dispatcher in LocatorBuilder.robot — no other wiring required.
...    The strategy name must also be used as the LocatorStrategy value in ObjectRegistry YAMLs.
...
...    Required keyword signature:
...        [Arguments]    ${properties}    ${page}    ${extension}=${EMPTY}
...        [Return]    <xpath or playwright locator string>
...
...    Example — locate by data-testid attribute:
...
...        Build Locator: ByDataTestId
...            [Arguments]    ${properties}    ${page}    ${extension}=${EMPTY}
...            [Return]    //*[@data-testid="${properties.Name}"]${extension}
