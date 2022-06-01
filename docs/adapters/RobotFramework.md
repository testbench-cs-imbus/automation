# **Robot Framework Adapter**

The Robot Framework Adapter is used to trigger existing Robot Framework Test Cases from TestBench CS and run them on your local machine. The Robot Framework listener reports the results step by step into TestBench CS.

## **Setup**

1. Fill in the variables in the config file in the "Robot Framework" section:

    ```bash
        "base_dir" # base directory - has to be an absolute path
        "search_dir" # path to the robot files
        "result_dir" # relative path where the result files should be stored
        "clean_up" # True or False, whether to delete the created files
    ```

2. Create Test Cases that have the same name as the Robot Framework Test Cases you want to execute

3. Set Custom Field value for Test Tool in each Test Case to "RobotFramework" or change variable **Default Adapter** in config to "RobotFramework"

## **How it works**

For each Test Case submitted by the Agent, the Adapter searches for Robot Framework Test Cases with the same name in the directory you defined in the config file and executes them. The Robot Framework Listener reports the results step by step into  TestBench CS. The adapter outputs an error message to the console if it cannot find the Test Case or if one or more errors occurred.
