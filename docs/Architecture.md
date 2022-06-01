# Architecture

In the whole process are 4 participants involved to automatically execute Test Suites and upload the test results into TestBench&nbsp;CS:

## TestBench CS

It contains the Test Suites and Test Cases and after all tests finished also a Test Session

```mermaid
classDiagram
  class TestBench CS {
    +get_products(): json
    +get_suites(product_id: int): json
    +get_suite(product_id: int, suite_id: int): json
    +post_session(product_id: int, name: String): int
    +join_session(product_id: int, session_id: int): void
    +get_test_case(product_id: int, test_case_id: int): json
    +post_execution(product_id: int, test_case_id: int): int
    +add_execution_to_session(product_id: int, session_id: int, test_case_id: int, execution_id: int): void
    +patch_session(product_id: int, session_id: int, json: json): void
    +patch_suite(product_id: int, suite_id: int, json: json): void
  }
```

---

## Agent

Communicates between TestBench&nbsp;CS and the Adapters. It is also responsible for fetching the Test Cases and writing the results back

```mermaid
classDiagram
  class Agent {
    -CONFIG_PATH: String
    -TBCS_BASE: String
    -ACCOUNT_WORKSPACE: String
    -ACCOUNT_LOGIN: String
    -ACCOUNT_PASSWORD: String
    -SESSION_PREFIX: String
    -PRODUCT_FILTER: String
    -tbcs: TbcsApi

    -read_config(CONFIG_PATH: String): void
    -connect_itb(): TbcsApi
    -is_matching(item_dict: dict, filter_dict: dict): boolean
    -get_products(tbcs: TbcsApi, PRODUCT_FILTER: String): list
    -get_test_suites(tbcs: TbcsApi, product_id: int, TEST_SUITE_FILTER: String): list
    -execute_test_list(tbcs: TbcsApi, product_id: int, test_suite: json, test_case_list: list): void
    -create_test_session(tbcs: TbcsApi, product_id: int): int
    -execute_test_case(tbcs: TbcsApi, product_id: int, test_session_id: int, test_case: json): list
    -get_attachements(test_case: json): String
    -collect_test_results(running_tests: list): void
  }
```

---

## Adapter

Receives Test Case from Agent and runs it on the specified Test Tool

```mermaid
classDiagram
  class Adapter {
    <<Interface>>
    #custom_fields

    #read_custom_fields()
    #execute()
    #get_result()
  }

  class RobotFramework {
    
  }

  class Carla {
    
  }

  class CarMaker {
    
  }

  Adapter <|-- RobotFramework
  Adapter <|-- Carla
  Adapter <|-- CarMaker
```

---

## Test Tool

The tool, which will be used for testing.
