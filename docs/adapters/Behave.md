# **Behave Adapter**

The Behave Adapter is used to generate Gherkin scenario files from TestBench CS and run them on your local machine using Behave. Results will be extracted from Behave output and in TestBench CS, the Test Case Exceution will reflect the result of each step.

## **Setup (Behave)**

1. Fill in the variables in the config file in the "Behave" section:
    

```bash
    "base_dir"      # base directory - should be an absolute path
    "result_dir"    # relative to base_dir, the place to store results
    "scenario_dir"  # relative to base_dir, the place to store scenario files, 
                    # and for Behave, where to find them 
    "cleanup"       # if True, remove generated files; otherwise leave them for further reference
```

2. In TB-CS, create Test Cases based on existing steps. Behave will expect these steps to be implemented in a file in the subfolder "steps" in your *scenario_dir*. You may consider to import existing steps from this folder using the script "import_steps_bdt.py", so in TB-CS you have them available as Keywords.

3. Set Custom Field value for Test Tool in each Test Case to "Behave" or change variable **Default Adapter** in config to "Behave"

## **How it works (Behave)**

For each Test Case submitted by the Agent, the Adapter creates a scenario file in the folder *scenario_dir*. Behave is triggered to run that scenario and writes the results into a file which is then read by the adapter. The adapter reports the results for each step into TestBench CS. 
