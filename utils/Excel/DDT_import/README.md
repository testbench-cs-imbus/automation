# DDT table import via Excel for TestBench CS

## Objective:
Import a data table to TestBench CS and attach to an existing Test Case.

This is a sample for using the TestBench CS API.

## Preconditions:
* Account for TestBench CS  workspace (free BASIC account is available at http://www.testbench.com)
* One or more products are available, containing at least one Test Case
* Excel VBA macro execution is admitted

## How to install:
* place the two files (.xls and .ini) in a folder
* edit `import_settings_table.ini` file. You need to replace placeholders for workspace, login,  password and product.

## How to use:
* Edit data table in sheet "Test Data" as required

To start import:
* in the Excel file in sheet "Control", fill in the ID of the Test Case you want to use (cell `B14`). Make sure the Test Case is not data driven yet! 
* Press the button "`Import table to TB-CS`". 
* In the popup, check the credentials (they are taken from the `.ini` file) and adjust them if necessary
* Click "Login" to proceed
* A new table is created and the ID of the table is written into cell `B13`
* IDs for columns/rows are written into the sheet "Test Data" (required for readin table)

To read a table from TestBench CS:
* make sure the table ID is written into cell `B13` (from import)
* In the popup, check the credentials (they are taken from the `.ini` file) and adjust them if necessary
* Click "Login" to proceed
* The table is read from TB-CS and the values replace the existing sheet "Test Data"

To delete a table in TestBench CS:
* make sure the table ID is written into cell `B13` (from import)
* In the popup, check the credentials (they are taken from the `.ini` file) and adjust them if necessary
* Click "Login" to proceed
* The table is deleted from TB-CS. The Test Case is not data-driven any more. All IDs (table, rows, colums) are reloved from the spreadsheet.




