# Cypress Specification and Result Import for TestBench CS

## Content

* [Prerequisites](#prerequisites)
* [Cypress Specification Import](#cypress-specification-import)
* [Cypress Result Import](#cypress-result-import)

See also:

* [cypress](https://www.cypress.io/)
* [TestBench CS](https://www.testbench.com/)

## Prerequisites

* An account in TestBench CS with at least "Test Analyst" rights. To create one, see here. <https://testbench.com>. For test result imports at least "Tester" rights are required too.
* If you want to run the script `import_cypress.py`, Python installation >= 3.8.10.
* If you want to execute the example tests provided, npm >= 6.13.4.

### Required TestBench CS data for imports

* Your workspace name, user name and password
* Your product ID

```script
  This one can be read out from the URL (the number after the string '/products/') after you have opened a product in your workspace. For example:
  https://https://cloud01-eu.testbench.com/en/products/5/home
```

## Cypress Specification Import

Parse cypress specification files and import generated test cases into TestBench CS.

The script `import_cypress.py` generates test cases out of cypress specifications. Given the following example it will create one user story and two test cases. The user story is imported to TestBench CS within a general Epic. The Epic name can be given as parameter (see [Usage](#Usage)).

```ts
describe("Login", () => {
  it("is not possible after password reset.", () => {
    cy.log("Enter valid user name.");
    // ...
    cy.log('Click the "Forgot Password" button.');
    // ...
    cy.log('Click the "Reset" button.');
    // ...
    cy.log("Enter the old password.");
    // ...
    cy.log('Click the "Login" button.');
    // ...
    cy.log('Check the error message: "Please enter ...".');
    // ...
  });
  //...
  it("should be possible after changing my password at first login.", () => {
    //...
  });
  //...
});
```

Result:

* Epic (default name):
  + User Story: Login
    - Test Case 1: Login is not possible after password reset.
      * Test Steps:
        * Enter valid user name.
        * Click the "Forgot Password" button.
        * Click the "Reset" button.
        * Enter the old password.
        * Click the "Login" button.
        * Check the error message: "Please enter ...".
    - Test Case 2: Login should be possible after changing my password at first login.

### Usage

The following example calls are all written for the Unix bash.

```bash
# list all possible parameter
python import_cypress.py -h
```

To configure your TestBench CS account information, you can also use a config.py file as described in [README.md](../../README.md).

The following example recursively parses all cypress specification files under the folder, given as arguments. It scans for specification files in the file or folder paths which can be multiple. After all files have been parsed the import of the results to the given TestBench CS instance is started.

```bash
python import_cypress.py --server https://cloud01-eu.testbench.com --workspace <workspace> --user <user> --password <pw> ./examples/cypress/tests
```

To check the test cases that will be generated before importing them you can use the -dry-run parameter like the following example shows.

```bash
python import_cypress.py -d ./examples/cypress/tests
```

### Example

You can find example tests in the `./examples/cypress` folder. To run it see [Prerequisites](#prerequisites)

```bash
cd example
npm install
# run cypress interactively
npm run cy-open
# or run cypress directly
npm run cy-run
```

## Cypress Result Import

Run within a regular cypress test execution and import test results to TestBench CS.

Before you activate the cypress result imports you are suggested to import your test cases with `import_cypress.py` before (see above). This will ensure a correct import structure but is not required. However if no test cases are found in TestBench CS matching an cypress test they will be created during the execution result import.

### Activation

Because the result import integration run within each cypress test run you will only have to setup your TestBench CS connection information and activate a flag that enables it like in the following example.

Configuration is done in file ./examples/cypress/cypress.json

```json
{
  ...
  "integrationFolder": "tests",
  "reporter": "junit",
  "reporterOptions": {
    "serverUrl": "https://cloud01-eu.testbench.com",
    "workspace": "<workspace>",
    "username": "<login>",
    "password": "<password>",
    "productId": "<product id>",
    "testSessionPrefix": "CYPRESS",
    "skipResultImport": false,
    "skipTestCaseUpdates": false
  },
  ...
}
```

The line `"skipResultImport": false` finally activates the result import.

Now you can run your tests as usual and your test results then can be found in TestBench CS. See also [Example](#Example)

If result import is enabled a file examples/cypress/testSessionId.txt is created after a cypress run and not automatically deleted at the end. To ensure that reporting creates a new test session, this file must be deleted before cypress run.

### Integration in your own Cypress installation

Simply copy the content of the examples/cypress/cypress folder from this repository into your equivialent cypress installation folder and extend your cypress.json file with the `reporterOptions` . Finally check that the file examples/cypress/cypress/tsconfig.json matches your settings too.

Thats it.
