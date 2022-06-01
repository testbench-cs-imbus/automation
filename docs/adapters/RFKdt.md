# **Robot Framework Keyword-Driven Testing Adapter**

The Robot Framework (RF) Keyword-Driven Testing (KDT) Adapter ("RFKdt") is used to generate Robot Framework ".robot" files from TestBench CS and run them on your local machine using Robot Framework. Results will be reported into TestBenh CS step by step.

## **Setup (Robot Framework for KDT)**

1. Fill in the variables in the config file in the "Robot KDT" section:
    

```bash
    "base_dir"      # base directory - should be an absolute path
    "script_dir"    # relative to base_dir, the place to store .robot files in, 
                    # and for Robot Framework, where to find them
    "result_dir"    # relative to base_dir, the place to store results
    "resource_dir"  # relative to base_dir, the place for .resource files
    "empty_string"  # used to indicate an empty a value for an argument
    "clean_up"      # True or False, whether to delete the created files
```


2. In TB-CS, create Test Cases based on existing Robot Framework Keywords. Robot Framework will expect these Keywords either to be defined within a resource file in your *resource_dir*, or in a library. If the attribute "library" in your Keywords within TB-CS is set properly, teh adapter makes sure to refernce the proper library or resource file in the generated robot file. You may consider to import existing Keywords using the script "import_kwd_rf.py", so in TB-CS you have them available as Keywords, with the proper settings on library/resource.

3. Set Custom Field value for Test Tool in each Test Case to "RFKdt" or change variable **Default Adapter** in config to "RFKdt"

4. If you wanne use the vsr example you need to install an additionall library for Robot Framework `pip install robotframework-browser` and `rfbrowser init`, see https://robotframework-browser.org/

## Steps and Keywords

Only structured Test Cases can be used for test automation with Robot Framework.
Both conventional test steps in prose or Keywords can be used in TestBench CS.

### Prose test steps: 
Specify steps like you would do in Robot Framework, separating arguments with blank spaces from the Keyword, e.g.:
```bash 
new browser    chromium    headless=false 
```
It's up to you to make sure that your text matches RF conventions.

### Keyword test steps:
Use Keywords to define test steps. Best practice is to import Keywords from .resource files or libraries. This way you can be sure that all used Keywords are defined in Robot Framework.

### Resources and Libraries:
If you are using Keywords, this adapter will use the attribute "library" to make sure the right resource files or libraries are included by the Robot Framework script.

To decide whether a library or a resource file is home of the Keyword, a prefix - one of "library" and "resource" - is used. The prefix may be abbreviated. If no prefix is given, resource is assumed. To separate the prefix from the library/resource-name, use a colon ":".

Examples:

* `lib:Browser` -> use library "Browser"
* `resource:myFile` -> use resource "myFile"
* `myFile` -> same as above: use resource "myFile"

If you are not using Keywords in your TestBench Test Cases, but prose test steps instead, you can specify the source by appending it to the Keyword, separated by a pair of percent characters: "%%"

Example:
* `download%%lib:Browser` -> use library "Browser"

You need to do that only once for each library or resource file in a test case.

(!) Mind: This adapter expects all resource files to sit in the defined resource folder "resource_dir"

## Arguents and Values

For Keywords with many arguments, often not all them are required.
If in TestBech you don't provide a value for a Keyword parameter, this parameter will not be provided in the generated Robot Framework file.

To explicitely provide an empty value, use the string defined in "empty_string", e.g. `_void_`.


## **How it works (Robot Framework Keyword-Driven Testing)**

For each Test Case submitted by the Agent, the Adapter creates a .robot file in the folder *script_dir*. Keywords in a section "Preparation" or "Setup" will be assigned to RF *[Setup]*. Keywords in a section "Cleanup", "Teardown" or "Reset Environment" will be assigned to RF *[Teardown]*. Robot Framework is triggered to run that test case. Using the Robot Framework Listener, it reports the results step by step into TestBench CS.
