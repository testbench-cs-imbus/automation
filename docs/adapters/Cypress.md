# **Cypress Adapter**

The Cypress Adapter is used to trigger existing Cypress Test Cases from TestBench CS and run them on your local machine.

## **Setup (Cypress)**

1. Fill out the variables in the config file in the "CYPRESS" section (the following settings use the existing example):
    

```bash
    "base_dir": "./examples/cypress",  # cypress root folder
    "result_dir": "./test-results", # relative path where the result files should be stored
    "cypress_bin": "./node_modules/.bin/cypress",  # e.g.: ./node_modules/.bin/cypress
    "cypress_spec_folder": "./tests",
    "cleanup": False, # True or False, whether to delete the created files
```

If you use the example and/or Cypress result reporting provided with the example, set the following option in `cypress.json` to ensure that also test step results are set in TestBench CS.

```bash
    "skipResultImport": false,
```

2. Create Test Cases that have the same External ID as the Cypress Test Cases you want to execute. See [import_cypress.md](../../docs/importers/import_cypress.md)

3. Set Custom Field value for Test Tool in each Test Case to "Cypress" or change variable **Default Adapter** in config to "Cypress"

## **How it works (Cypress)**

For each Test Case given by the Agent, the Adapter searches for Cypress Test Cases with the same External ID in the directory you defined in the config file and executes them. Depending on the reporting variable, it either uses the Cypress reporting to report the results step by step or only report the final result of every Test Case back into TestBench CS. The adapter outputs an error message to the console if it cannot find the Test Case or if one or more errors occurred.
