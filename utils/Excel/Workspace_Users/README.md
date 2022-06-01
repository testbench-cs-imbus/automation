# Setup users along with Workspaces in TestBench CS

## Objective:
Quickly create users in TestBench CS and add them to up to two newly created workspaces.

This is a sample for using the TestBench CS API.

## Preconditions:
* Account for TestBench CS  workspace (free BASIC account is available at http://www.testbench.com)
* Excel VBA macro execution is admitted
* Sufficient licenses for the users that are supposed to be created

## How to install:
* place the two files (.xls and .ini) in a folder
* edit .ini file. You need to replace placeholders for workspace, login and password.

## How to use:
* In the Excel file in sheet "`UserList`", for each user to be created fill in a line. Column specifications see below 
* In the Excel file in sheet "`Control`", just press the button "`Run Export from TB-CS`".
* In the popup, check the credentials (they are taken from the `.ini` file) and adjust them if necessary
* Click "Login" to proceed
* For each line in sheet "`UserList`", a user is created, provided that the User does not exist, and sufficient licenses are available.

## Column specifications
In Sheet  "`UserList`", the following columns are available:

### Input, provided by you:

* `Name`: Name of the User to be displayed in TestBench
* `Login`: Login-name of the user to be used in login-dialog
* `Password`: User password for login. Please make sure to use a valid password, or creating the user may fail.
* `Testmanager`: If the value is `X`, the user will get the role "Testmanager" assigned.
* `Testanalyst`: If the value is `X`, the user will get the role "Testanalyst" assigned.
* `Tester`: If the value is `X`, the user will get the role "Tester" assigned.
* `Email`: User email address - make sure it's valid, the user will receive a mail after creation in TestBench.
* `Change Pwd`: if set to `1`, the user is required to change password at first login.
* `Product1`: name of the first product the new user is assigned to. If the Product does not exist, a new product with this name is created.
* `Product2`: name of the decond product the new user is assigned to. If the Product does not exist, a new product with this name is created.
* `Create XT?`: if set to `1`, an exploratory testing session is created in `Product1`, and the user is added in this session.


### Output:
* `out: UID`: TestBench User ID for newly created user (filled in after creation).
* `out: ID Product 1`: TestBench Product ID for `Product1`.
* `out: ID Product 2`: TestBench Product ID for `Product2`.
* `out: ID Session`: TestBench ID for exploratory testing session.


