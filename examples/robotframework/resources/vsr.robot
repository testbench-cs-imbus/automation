*** Settings ***
Documentation     Reusable keywords and variables.
Library           Browser
Library           Dialogs
Library    XML

*** Variables ***
${VSR_URL}       https://vsr.testbench.com/login
${BROWSER_TYPE}  chromium

*** Keywords ***

Open VSR
    [Documentation]    Open VSR Base page
    New Browser    ${BROWSER_TYPE}    headless=false
    New Page        ${VSR_URL} 
    sleep      3
    VSR should be Open


VSR should be Open
    Get Url    matches     ${VSR_URL} 
    Get Title    ==        VirtualShowRoom II

Login as customer
    Click    text="As Customer"
    Get Url    matches     https://vsr.testbench.com/dreamcar/list
    Sleep    2

Goto Basemodel
   Click    text="Basemodel"
   Get Url    matches    https://vsr.testbench.com/dreamcar/basemodel
   sleep     1

Goto Summary
   Click    text="Summary"
   Get Url    matches    https://vsr.testbench.com/dreamcar/summary
   sleep     1

Goto Engine
    Click    text="Engine"
    Get Url    matches    https://vsr.testbench.com/dreamcar/engine
    sleep     1

Check Price    
    [Arguments]    ${price}
    Get Text    xpath=//*[@id="label_price_sum"]    matches    ${price}

press button Order
    Click    text="Order"
    Get Url    matches    https://vsr.testbench.com/justintime/order
    sleep     1

press button Finance
    Click    text="Financing"
    Get Url    matches    https://vsr.testbench.com/easyfinance/installment
    sleep     1

press button Insurance
    Click    text="Insurance"
    Get Url    matches    https://vsr.testbench.com/norisk/insurance
    sleep     1

close
    Click    text="Logout"