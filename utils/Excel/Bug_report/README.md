# Defect Export via Excel for TestBench CS

## Objective:
Export recorded defects from TestBench CS into Excel for further processing.

This is a sample for using the TestBench CS API.

## Preconditions:
* Account for TestBench CS  workspace (free BASIC account is available at http://www.testbench.com)
* One or more products are available, and contain defect reports
* Excel VBA macro execution is admitted

## How to install:
* place the two files (.xls and .ini) in a folder
* edit .ini file. You need to replace placeholders for workspace, login and password.

## How to use:
* In the Excel file in sheet "Control", just press the button "`Run Export from TB-CS`".
* In the popup, check the credentials (they are taken from the `.ini` file) and adjust them if necessary
* Click "Login" to proceed
* For each product accessible with the used credentials, a worksheet wil be created, listing all defect reports in that product.

