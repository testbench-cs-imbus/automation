# **Importing Test Cases / Test Suites from Robot Framework**

The script `import_tc_rf.py` is used to import Test Cases from Robot Framework (RF) files into TestBech CS.

## **How to use**

Call the importer script, e.g.:

```bash
python .\import_tc_rf.py source [-tc "Test Case name" [, ...]]
```

The parameter `source` can be either a path to one or more filenames of a `.robot` file or one or more paths to directories containing `.robot` files.

The script will list all available products in your workspace and prompt to select one. Enter the ID of the product of your choice (leading number).

Import starts.

## **Command line flags**

| options | explanation |
| -------| --- |
  -h, --help | show this information and exit
  -w WORKSPACE, --workspace WORKSPACE | your TestBench CS workspace
  -s SERVER, --server SERVER | base address for TestBench CS Server
  -u USER, --user USER | user name for accessing TestBench CS
  -p PASSWORD, --password PASSWORD | password for accessing TestBench CS
  -i, --insecure | for debugging only: ignore SSL warnings
  -tc --testcase | only those Test Cases will be imported

## **Security issues**

You may want to avoid exposing your credentials (server, workspace, username and password) to access TestBench CS. Depending on your requirements, for each of those you can choose between three options for a balance between comfort and confidentiality:

* Store your credentials in the file `config.py` you create based on `config.py.template`
* Provide your credentials on the command line (see above)
* If you leave one or more credentials empty in the config file, and do not provide them in the command line, the script will prompt you.

## **How it works (RF Test Case Import)**

This script collects all required data from a Robot Framework Test Case and uploads this information to TestBench CS.
The importer operated in several stages:

Preparation:

* If the custom field  named according to config variable "`ADAPTER_CUSTOM_FIELD_NAME`" does not exist in TestBench CS, it is created. (see Limitations)

Create / Update Test Case(s):

* check if the Test Case exists in TestBench CS
* create a new Test Case if it doesn't already exist, otherwise update it
* set `externalId` if robot Test Case contains a Tag starting with "`ID:`"
* set `description` if robot Test Case has a `Description` section
* set `isAutomated` and `toBeReviewed` to `True`
* if not found, 3 test step sections are created (Setup, Test Steps, Teardown)

Import Test Steps as Keywords or Text Steps:

* control type of steps to be created via "`TEST_STEP_TYPE`" in config ("`Keyword`" or "`TextStep`")
* within the sections in the test sequence, steps will accordingly be either created as Keywords or as Text Steps

Creating Keywords:

* if a Keyword is required for the test sequence, creates a new Keyword (unless it already exists)
* if available, add the `description` for that Keyword
* adding the required `parameters` for that Keyword
* setting the flag `isImplemented` to true
* set the proper value for `library`

## **Limitations**

* Keyword descriptions longer than 3999 characters are truncated since this is a limit in TestBench CS.
* The script tries to create custom fields if required. This will fail if the configured user is not an administrator in the product.