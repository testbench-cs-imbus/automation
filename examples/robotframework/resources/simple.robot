*** Settings ***
Documentation     Simple Reusable keywords and variables.

*** Variables ***
${result}    0

*** Keywords ***
Log Something
    [Documentation]    Print ${text}
    [Arguments]    ${text}
    Log To Console    ${text}

Magic Additon
    [Documentation]    Magically adds a to b and saves the result
    [Arguments]    ${a}  ${b}
    ${x} =    Catenate    ${a}${b}
    Set Suite Variable    ${result}  ${x}

Magic Result Check
    [Documentation]    Checks the given value with the saved result
    [Arguments]    ${value}
    Should Be Equal    ${result}  ${value}
