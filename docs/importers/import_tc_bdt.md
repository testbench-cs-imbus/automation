# **Importing Test Cases from Gherkin/Behave**

The script `import_steps_bdt.py` is used to import Test Cases from Behave `*.feature` files into TestBech CS.

## **Setup (Behave Steps/Keyword Import)**

Fill in the variables in the config file in the "Behave" section:

```bash
    "base_dir"      # base directory - should be an absolute path
    "result_dir"    # relative to base_dir, the place to store results
    "scenario_dir"  # relative to base_dir, the place to store scenario files, 
                    # and for Behave, where to find them 
    "cleanup"       # if True, remove generated files; otherwise leave them for further reference
```

For import, actually only `base_dir` and `scenario_dir` are required; these seetimgs are shared with the adapter Behave.



## **How to use**

Call the importer script, e.g.:

```bash
python .\import_tc_bdt.py source_file 
```

The parameter `source_file` is either a feature folder (import all features/scenarios in that folder), or the filename of the `*.feature` file to be imported.

The script will list all available products in your workspace and prompt to select one. Enter the ID of the product of your choice (leading number).

Import starts.

## **Command line flags**

| options | explanation |
| -------| --- |
  -h, --help  |          show this information and exit
  -t {text, keyword}, --type {text, keyword} |    type of test steps to be created
  -w WORKSPACE, --workspace WORKSPACE |       your TestBench CS workspace
  -s SERVER, --server SERVER |                        base address for TestBench CS Server
  -u USER, --user USER | user name for accessing TestBench CS
  -p PASSWORD, --password PASSWORD |                        password for accessing TestBench CS
  -i, --insecure     |   for debugging only: ignore SSL warnings

## **Security issues**

You may want to avoid exposing your credentials (server, workspace, username and password) to access TestBench CS. Depending on your requirements, for each of those you can choose between three options for a balance between comfort and confidentiality:

* Store your credentials in the file `config.py` you create based on `config.py.template`
* Provide your credentials on the command line (see above)
* If you leave one more credentials empty in the config file, and do not provide them in the command line, the script will prompt you.

## **How it works (Behave Steps/Keyword Import)**

This script takes advantage of  the capability of "behave" to list available features and scenarios. For each feature, a User Story is created in TestBench CS, in the selected product. For each scenario, a Test Cases is added.

Preparation:

* If the custom field  named according to config variable "`ADAPTER_CUSTOM_FIELD_NAME`" does not exist in TestBench CS, it is created. (see Limitations)

Actual creation of Test Case(s):

* Test Cases are created using sections `GIVEN`,  `WHEN` and `THEN`.
* Steps in this sections are created as either prose text, or as Keywords, depending on the flag `--type`. Tip: if you want to use inline parameters, text steps may be preferable; Otherwise Keywords have the advantage of better reusability.

## **Limitations**

* Nested features are not supported
* Behave will always list all scenarios in a feature, so importing a subset is not possible.
* Data tables in `*.feature` files are currently not imported
* The script tries to create custom fields if required. This will fail if the configured user is not an administrator in the product.
