from typing import Dict, List, Union

import requests


class TbcsApi:
    # False for playground testing, True for production use
    verify = True  # False

    # the current test session id if one created for external access
    test_session_id: str = ""
    session_token: str = ""
    product_id: str = ""
    tenant_id: str = ""

    keyword_list: dict = {}

    @staticmethod
    def setup(tbcs_base: str, workspace: str, login: str, password: str) -> 'TbcsApi':
        """
        Logs the user into the given workspace.

        Parameters
        ----------
        tbcs_base: str
            Base url of TestBench CS
        workspace: str
            Tenant name 
        login: str
            Username
        password: str
            Password of the user

        Returns
        -------
        TbcsApi
            A new instance of a TestBench CS Api
                
        Notes
        -----
        For more information visit:

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Login/post_api_tenants_login_session
        """
        route_login = f"{tbcs_base}/api/tenants/login/session"
        login_body = {'tenantName': workspace, 'login': login, 'password': password, 'force': True}
        login_response = requests.post(route_login,
                                       json=login_body,
                                       headers={'Content-Type': 'application/json'},
                                       verify=TbcsApi.verify)
        assert login_response.status_code == 201, f"Login failed: {login_response.text}"
        tenant_id = str(login_response.json()['tenantId'])
        user_id: str = str(login_response.json()['userId'])
        session_token: str = login_response.json()['sessionToken']
        return TbcsApi(tbcs_base, tenant_id, user_id, session_token)

    def __init__(self, tbcs_base: str, tenant_id: str, user_id: str, session_token: str):
        """
        Initializes the TbcsApi class.

        Parameters
        ----------
        tbcs_base: str
            Base url of TestBench CS
        tenant_id: str
            Id of the tenant
        user_id: str
            Id of the user
        session_token: str
            Session token of the logged in user

        Returns
        -------
        TbcsApi
            A new instance of a TestBench CS Api
        """
        self.tbcs_base = tbcs_base
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.session_token = session_token
        self.rest_header = {'Content-Type': 'application/json', 'Authorization': session_token, 'encoding': 'utf8'}
        self.form_data_header = {'Authorization': session_token, 'Accept': 'application/json'}
        self.tenant_route = f"{tbcs_base}/api/tenants/{tenant_id}"

    def get_products(self) -> Dict[str, Union[str, int, List[str]]]:
        """
        Returns all products of a specific tenant.

        Parameters
        ----------
        None

        Returns
        -------
        dict
            Dictionary containing all products of a tenant
                
        Notes
        -----
        For more information visit:

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Products/get_api_tenants__tenantId__products
        """
        route = f"{self.tenant_route}/products"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET products failed: {response.text}"
        return response.json()

    def __product_route(self, product_id: str) -> str:
        """
        Concatenate tenant route with product id.

        Parameters
        ----------
        product_id: str
            Id of the product

        Returns
        -------
        str
            Full product route
        """
        return f"{self.tenant_route}/products/{product_id}"

    def get_server(self) -> Dict[str, str]:
        """
        Returns server info.

        Parameters
        ----------

        Returns
        -------
        dict
            Dictionary containing info on server: `serverversion` and `marketPlaceUrl`
                
        Notes
        -----
        For more information visit:

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Static%20Calls/get_api_serverInfo
        """
        route = f"{self.tbcs_base}/api/serverInfo"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET server info failed: {response.text}"
        return response.json()

    def get_suites(self, product_id: str) -> Dict[str, Union[str, int]]:
        """
        Returns all Test Suites from a given product.

        Parameters
        ----------
        product_id: str
            Id of the product

        Returns
        -------
        dict
            Dictionary containing all Test Suites of a product
                
        Notes
        -----
        For more information visit:

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/test-planning/openapi.yaml#/Test%20Suite/getTenantTestSuites
        """
        route = f"{self.__product_route(product_id)}/planning/suites/v1"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET suites failed: {response.text}"
        return response.json()

    def get_suite(self, product_id: str, suite_id: str) -> dict:
        """
        Returns the content of a specific Test Suite.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        suite_id: str
            Id of the Test Suite

        Returns
        -------
        dict
            Dictionary containing all informations of a specific Test Suite
                
        Notes
        -----
        For more information visit:

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/test-planning/openapi.yaml#/Test%20Suite/getTenantTestSuite
        """
        route = f"{self.__product_route(product_id)}/planning/suites/{suite_id}/v1"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET suite {suite_id} failed: {response.text}"
        return response.json()

    def post_suite(self, product_id: str, name: str) -> str:
        """
        Creates a new Test Suite in TestBench CS.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        name: str
            Name of the new Test Suite

        Returns
        -------
        str
            Id of the new created Test Suite
            
        Notes
        -----
        For more information visit:

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/test-planning/openapi.yaml#/Test%20Suite/postTenantTestSuite
        """
        route = f"{self.__product_route(product_id)}/planning/suites/v1"
        response = requests.post(route, json={'name': name}, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 201, f"POST suite failed: {response.text}"
        return str(response.json()['testSuiteId'])

    def patch_suite(self, product_id: str, suite_id: str, body: dict) -> None:
        """
        Updates the content of a Test Suite.

        Parameters
        ----------
        product_id: str
            Id of the product

        suite_id: str
            Id of the Test Suite
            
        body: dict
            Dictionary with content that should be updated

        Returns
        -------
        None
            
        Notes
        -----
        For more information visit:

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/test-planning/openapi.yaml#/Test%20Suite/patchTenantTestSuite
        """
        route = f"{self.__product_route(product_id)}/planning/suites/{suite_id}/v1"
        response = requests.patch(route, json=body, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"PATCH suite {suite_id} failed: {response.text}"

    def get_sessions(self, product_id: str) -> dict:
        """
        Returns all Test Sessions from a given product.

        Parameters
        ----------
        product_id: str
            Id of the product

        Returns
        -------
        dict
            Dictionary containing all Test Sessions of a product
            
        Notes
        -----
        For more information visit:

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/test-planning/openapi.yaml#/Test%20Session/getTenantTestSessions
        """
        route = f"{self.__product_route(product_id)}/planning/sessions/v1"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET all sessions failed: {response.text}"
        return response.json()

    def get_session(self, product_id: str, session_id: str) -> dict:
        """
        Returns the content of a specific Test Session.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        session_id: str
            Id of the Test Session

        Returns
        -------
        dict
            Dictionary containing all informations of a specific Test Session
            
        Notes
        -----
        For more information visit:

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/test-planning/openapi.yaml#/Test%20Session/getTenantTestSession
        """
        route = f"{self.__product_route(product_id)}/planning/sessions/{session_id}/v1"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET session failed: {response.text}"
        return response.json()

    def post_session(self, product_id, name: str) -> str:
        """
        Creates a new Test Session in TestBench CS.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        name: str
            Name of the new Test Session

        Returns
        -------
        str
            Id of the new created Test Suite
            
        Notes
        -----
        For more information visit:

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/test-planning/openapi.yaml#/Test%20Session/postTenantTestSession
        """
        route = f"{self.__product_route(product_id)}/planning/sessions/v1"
        response = requests.post(route, json={'name': name}, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 201, f"POST session failed: {response.text}"
        self.test_session_id = str(response.json()['testSessionId'])
        return self.test_session_id

    def patch_session(self, product_id: str, session_id: str, body: dict) -> None:
        """
        Updates the content of a Test Session.

        Parameters
        ----------
        product_id: str
            Id of the product

        session_id: str
            Id of the Test Session
            
        body: dict
            Dictionary with content that should be updated

        Returns
        -------
        None
        
        Notes
        -----
        For more information visit:

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/test-planning/openapi.yaml#/Test%20Session/patchTenantTestSession
        """
        route = f"{self.__product_route(product_id)}/planning/sessions/{session_id}/v1"
        response = requests.patch(route, json=body, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"PATCH session {session_id} failed: {response.text}"

    def delete_session(self, product_id: str, session_id: str) -> None:
        """
        Deletes a Test Session.

        Parameters
        ----------
        product_id: str
            Id of the product

        session_id: str
            Id of the Test Session

        Returns
        -------
        None
        
        Notes
        -----
        For more information visit:

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/test-planning/openapi.yaml#/Test%20Session/deleteTenantTestSession
        """
        route = f"{self.__product_route(product_id)}/planning/sessions/{session_id}/v1"
        response = requests.delete(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"Session remove failed: {response.text}"

    def join_session(self, product_id: str, session_id: str) -> None:
        """
        Current user joins the given Test Session.

        Parameters
        ----------
        product_id: str
            Id of the product

        session_id: str
            Id of the Test Session

        Returns
        -------
        None
        
        Notes
        -----
        For more information visit:

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/test-planning/openapi.yaml#/Test%20Session/joinAsParticipant
        """
        route = f"{self.__product_route(product_id)}/planning/sessions/{session_id}/participant/self/v1"
        response = requests.patch(route, json={'active': True}, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"JOIN session {session_id} failed: {response.text}"

    def add_execution_to_session(self, product_id: str, session_id: str, test_case_id: str, execution_id: str) -> None:
        """
        Adds an execution to a Test Session.

        Parameters
        ----------
        product_id: str
            Id of the product

        session_id: str
            Id of the Test Session

        test_case_id: str
            Id of the Test Case

        execution_id: str
            Id of the Test Execution

        Returns
        -------
        None
        
        Notes
        -----
        For more information visit:

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/test-planning/openapi.yaml#/Test%20Session/assignExecutions/
        """
        route = f"{self.__product_route(product_id)}/planning/sessions/{session_id}/assign/executions/v1"
        body = {'addExecutions': [{'testCaseIds': {'testCaseId': int(test_case_id)}, 'executionId': execution_id}]}
        response = requests.patch(route, json=body, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"ADD execution to session {session_id} failed: {response.text}"

    def get_all_test_cases(self, product_id: str) -> dict:
        """
        Returns all Test Cases from a given product.

        Parameters
        ----------
        product_id: str
            Id of the product

        Returns
        -------
        dict
            Dictionary containing all Test Cases of a product
        
        Notes
        -----
        For more information visit:

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Specifications/get_api_tenants__tenantId__products__productId__specifications_testCases
        """
        route = f"{self.__product_route(product_id)}/specifications/testCases"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET all test cases failed: {response.text}"
        return response.json()

    def get_test_case(self, product_id: str, test_case_id: str) -> dict:
        """
        Returns the content of a specific Test Case.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        test_case_id: str
            Id of the Test Case

        Returns
        -------
        dict
            Dictionary containing all informations of a specific Test Case
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Specifications/get_api_tenants__tenantId__products__productId__specifications_testCases__testCaseId_/
        """
        route = f"{self.__product_route(product_id)}/specifications/testCases/{test_case_id}"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET test case {test_case_id} failed: {response.text}"
        return response.json()

    def get_test_case_by_filter(self, product_id: str, field: str, operator: str, filter: str) -> dict:
        """
        Searches for a specific Test Case by a filter.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        field: str
            Field whose values are to be filtered ('title', 'description', 'status' and 'externalId')

        operator: str
            Operator of the filter ('equals', 'not-equals', 'contains', 'not-contains')

        filter: str
            String that should be considered in the filtering

        Returns
        -------
        dict
            Dictionary containing all informations of a specific, filtered Test Case

        Notes
        -----
        For more information visit

        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Specifications/get_api_tenants__tenantId__products__productId__specifications_testCases
        """
        search_filter: str = f"fieldValue={field}:{operator}:{filter}"
        route = f"{self.__product_route(product_id)}/specifications/testCases?{search_filter}"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200 or response.status_code == 404, f"GET specific test case by filter failed: {response.text}"
        return response.json()

    def post_test_case(self, product_id: str, body: dict) -> str:
        """
        Creates a new Test Case in TestBench CS.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        body: dict
            Dictionary that must contain the following keys:
            - name: str
            - testCaseType: str (StructuredTestCase, ChecklistTestCase, SimpleTestCase)

        Returns
        -------
        str
            Id of the new created Test Case
            
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Specifications/post_api_tenants__tenantId__products__productId__specifications_testCases
        """
        route = f"{self.__product_route(product_id)}/specifications/testCases"
        response = requests.post(route, json=body, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 201, f"POST test_case failed: {response.text}"
        return str(response.json()['testCaseId'])

    def patch_test_case(self, product_id: str, test_case_id: str, body: dict) -> None:
        """
        Updates the content of a Test Case.

        Parameters
        ----------
        product_id: str
            Id of the product

        test_case_id: str
            Id of the Test Case
            
        body: dict
            Dictionary with content that should be updated

        Returns
        -------
        None
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Specifications/patch_api_tenants__tenantId__products__productId__specifications_testCases__testCaseId_/
        """
        route = f"{self.__product_route(product_id)}/specifications/testCases/{test_case_id}"
        response = requests.patch(route, json=body, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"PATCH test_case failed: {response.text}"

    def post_execution(self, product_id: str, test_case_id: str) -> str:
        """
        Creates a new Execution in TestBench CS.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        test_case_id: str
            Id of the Test Case

        Returns
        -------
        str
            Id of the new created Execution
            
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/executions/openapi.yaml#/Executions/startExecution/
        """
        route = f"{self.__product_route(product_id)}/executions/testCases/{test_case_id}/v1"
        response = requests.post(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 201, f"POST execution failed: {response.text}"
        return response.json()['executionId']

    def post_execution_ddt(self, product_id: str, test_case_id: str, table_id: str, row_id: str) -> str:
        """
        Creates a new Execution for Data-driven Test Cases in TestBench CS.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        test_case_id: str
            Id of the Test Case

        table_id: str
            Id of the table

        row_id: str
            Id of the row

        Returns
        -------
        str
            Id of the new created Execution
            
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/executions/openapi.yaml#/Executions/startConcreteTestCaseExecution/
        """
        route = f"{self.__product_route(product_id)}/executions/testCases/{test_case_id}/tables/{table_id}/rows/{row_id}/v1"
        response = requests.post(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 201, f"POST DDT execution failed: {response.text}"
        return response.json()['executionId']

    def patch_execution(self, product_id: str, test_case_id: str, execution_id: str, body: dict) -> None:
        """
        Updates the content of an Execution.

        Parameters
        ----------
        product_id: str
            Id of the product

        test_case_id: str
            Id of the Test Case
            
        execution_id: str
            Id of the Execution

        body: dict
            Dictionary with content that should be updated

        Returns
        -------
        None
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/executions/openapi.yaml#/Executions/patchExecution/
        """
        route = f"{self.__product_route(product_id)}/executions/testCases/{test_case_id}/executions/{execution_id}/v1"
        response = requests.patch(route, json=body, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 204, f"PATCH execution failed: {response.text}"

    def get_concrete_test_case(self, product_id: str, test_case_id: str, table_id: str, row_id: str) -> dict:
        """
        Returns a concrete Test Case from an abstract Test Case.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        test_case_id: str
            Id of the Test Case

        table_id: str
            Id of the table

        row_id: str
            Id of the row

        Returns
        -------
        dict
            Dictionary containing all informations of a concrete Test Case
            
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Specifications/get_api_tenants__tenantId__products__productId__specifications_testCases__testCaseId__table__tableId__row__rowId_/
        """
        route = f"{self.__product_route(product_id)}/specifications/testCases/{test_case_id}/table/{table_id}/row/{row_id}"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET concrete Test Case failed: {response.text}"
        return response.json()

    def get_ddt_table(self, product_id: str, test_case_id: str, table_id: str) -> dict:
        """
        Returns a Data-driven table.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        test_case_id: str
            Id of the Test Case

        table_id: str
            Id of the table

        Returns
        -------
        dict
            Dictionary containing all informations of a table
            
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/ddt/openapi.yaml#/Data-Driven%20Tables/getOneDDT
        """
        route = f"{self.__product_route(product_id)}/ddt/testCases/{test_case_id}/tables/{table_id}/v1"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET ddt table {table_id} failed: {response.text}"
        return response.json()

    def post_ddt_table(self, product_id: str, test_case_id: str, name: str) -> str:
        """
        Creates a Data-driven table.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        test_case_id: str
            Id of the Test Case

        name: str
            Name of the table

        Returns
        -------
        str
            Id of the new created table
            
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/ddt/openapi.yaml#/Data-Driven%20Tables/createDDT
        """
        route = f"{self.__product_route(product_id)}/ddt/testCases/{test_case_id}/v1"
        response = requests.post(route, json={'name': name}, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 201, f"POST ddt table failed: {response.text}"
        return str(response.json()['tableId'])

    def patch_ddt_table(self, product_id: str, test_case_id: str, table_id: str, body: dict) -> str:
        """
        Updates the content of a DDT table.

        Parameters
        ----------
        product_id: str
            Id of the product

        test_case_id: str
            Id of the Test Case
            
        table_id: str
            Id of the table

        body: dict
            Dictionary with content that should be updated

        Returns
        -------
        str
            Id of the new column
            
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/ddt/openapi.yaml#/Data-Driven%20Tables/updateOneDDT
        """
        route = f"{self.__product_route(product_id)}/ddt/testCases/{test_case_id}/tables/{table_id}/v1"
        response = requests.patch(route, json=body, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"PATCH ddt table {table_id} failed: {response.text}"
        return str(response.json()["columnId"])

    def get_ddt_row(self, product_id: str, test_case_id: str, table_id: str, row_id: str) -> List[dict]:
        """
        Returns all values of a single DDT row.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        test_case_id: str
            Id of the Test Case

        table_id: str
            Id of the table

        row_id: str
            Id of the row

        Returns
        -------
        List[dict]
            List of dictionaries containing all column - value pairs of one row: [{'column': 'colName', 'value': 'ddtValue'}, ...]       
        """

        #This method can be simplified when https://testbenchcs.atlassian.net/browse/ITB-5885
        #is completed.
        ddt_table = self.get_ddt_table(product_id, test_case_id, table_id)
        ddt_rows = ddt_table['rowData']
        ddt_cols = ddt_table['columnsMetaData']
        ddt_row = next(ddt_row['data'] for ddt_row in ddt_rows if ddt_row['id'] == row_id)
        return [{
            'column': next(ddt_col['name'] for ddt_col in ddt_cols if ddt_col['id'] == entry['columnId']),
            'value': entry['value']
        } for entry in ddt_row]

    def post_ddt_row(self, product_id: str, test_case_id: str, table_id: str) -> str:
        """
        Creates a Data-driven row.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        test_case_id: str
            Id of the Test Case

        table_id: str
            Id of the table

        Returns
        -------
        str
            Id of the new created row
            
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/ddt/openapi.yaml#/Data-Driven%20Tables/createRowInDDT
        """
        route = f"{self.__product_route(product_id)}/ddt/testCases/{test_case_id}/tables/{table_id}/rows/v1"
        response = requests.post(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 201, f"POST DDT Row to table {table_id} failed: {response.text}"
        return str(response.json()['rowId'])

    def patch_ddt_row(self, product_id: str, test_case_id: str, table_id: str, row_id: str, body) -> None:
        """
        Updates the content of a DDT row.

        Parameters
        ----------
        product_id: str
            Id of the product

        test_case_id: str
            Id of the Test Case
            
        table_id: str
            Id of the table
        
        row_id: str
            Id of the row

        body: dict
            Dictionary with content that should be updated

        Returns
        -------
        None
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/ddt/openapi.yaml#/Data-Driven%20Tables/updateRowInDDT
        """
        route = f"{self.__product_route(product_id)}/ddt/testCases/{test_case_id}/tables/{table_id}/rows/{row_id}/v1"
        response = requests.patch(route, json=body, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 204, f"PATCH DDT Row to table {table_id} failed: {response.text}"

    def get_file_response(self, product_id: str, file_id: str) -> requests.Response:
        """
        Downloads a specific file from TestBench CS and returns the request response.

        Parameters
        ----------
        product_id: str
            Id of the product

        file_id: str
            Id of the file

        Returns
        -------
        requests.Response
            The response from the GET call containing the content of the file
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/File/get_api_tenants__tenantId__products__productId__file_download
        """
        route = f"{self.__product_route(product_id)}/file/download?fileIds={file_id}"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET file {file_id} failed: {response.text}"
        return response

    def upload_file_to_execution(self, product_id: str, test_case_id: str, execution_id: str,
                                 path_to_file: str) -> dict:
        """
        Uploads a specific file into TestBench CS and attaches it to an Execution.

        Parameters
        ----------
        product_id: str
            Id of the product

        test_case_id: str
            Id of the Test Case

        execution_id: str
            Id of the Execution

        path_to_file: str
            Path to the file that should be uploaded

        Returns
        -------
        dict
            Dictionary containing fileId, name and size of the uploaded file
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/File/post_api_tenants__tenantId__products__productId__file_upload
        """
        route = f"{self.__product_route(product_id)}/file/upload?element=Execution&executionId={execution_id}&parentId={test_case_id}"
        response = requests.post(route,
                                 files={'formData': open(path_to_file, 'rb')},
                                 headers=self.form_data_header,
                                 verify=self.verify)
        assert response.status_code == 201, f"Upload file failed: {response.text}"
        return response.json()

    def upload_file_to_test_case(self, product_id: str, test_case_id: str, path_to_file: str) -> dict:
        """
        Uploads a specific file into TestBench CS and attaches it to a Test Case.

        Parameters
        ----------
        product_id: str
            Id of the product

        test_case_id: str
            Id of the Test Case

        path_to_file: str
            Path to the file that should be uploaded

        Returns
        -------
        dict
            Dictionary containing fileId, name and size of the uploaded file

        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/File/post_api_tenants__tenantId__products__productId__file_upload
        """
        route = f"{self.__product_route(product_id)}/file/upload?element=TestCase&elementId={test_case_id}"
        response = requests.post(route,
                                 files={'formData': open(path_to_file, 'rb')},
                                 headers=self.form_data_header,
                                 verify=self.verify)
        assert response.status_code == 201, f"Upload file failed: {response.text}"
        return response.json()

    def get_custom_field_containers(self) -> List[dict]:
        """
        Retrieve all custom fields containers.

        Parameters
        ----------
        None

        Returns
        -------
        List[dict]
            List of dictionaries containing all custom field containers of a tenant
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Custom%20Fields/get_api_tenants__tenantId__customFields_containers
        """
        route = f"{self.tenant_route}/customFields/containers"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET customFields failed: {response.text}"
        return response.json()

    def update_custom_field_containers(self,
                                       fieldList: List[int],
                                       container: str = "TestCase",
                                       anchor: str = "BeforeDescription") -> None:
        """
        Update a fields container.

        Parameters
        ----------
        fieldList: List[int]
            list of fields to be shown in container
        container: str
            Name of container to update. Valid: Epic, UserStory, TestCase, Execution, Defect, TestSuite, TestSession
        anchor: str
            Name of anchor (=position) of container. Valid, depending on container: BeforeDescription, BeforePreconditions, 
            BeforeTestExecutionHistory, BeforeTestSequence, BeforeTestExecution, BeforeAutomation, 
            BeforeTestCases, Bottom

        Returns
        -------
        None
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Custom%20Fields/put_api_tenants__tenantId__customFields_containers__container___anchor_
        """
        route = f"{self.tenant_route}/customFields/containers/{container}/{anchor}"
        response = requests.put(route, json=fieldList, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET customFields failed: {response.text}"

    def get_custom_field_list(self) -> List[dict]:
        """
        Retrieve all custom fields.

        Parameters
        ----------
        None

        Returns
        -------
        List[dict]
            List of dictionaries containing all custom fields of a tenant
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Custom%20Fields/get_api_tenants__tenantId__customFields_fields
        """
        route = f"{self.tenant_route}/customFields/fields"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET customFields failed: {response.text}"
        return response.json()

    def get_custom_field_block_list(self) -> List[dict]:
        """
        Retrieve all custom field blocks.

        Parameters
        ----------
        None

        Returns
        -------
        List[dict]
            List of dictionaries containing all custom field blocks of a tenant
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Custom%20Fields/get_api_tenants__tenantId__customFields_blocks
        """
        route = f"{self.tenant_route}/customFields/blocks"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET customFieldlocks failed: {response.text}"
        return response.json()

    def add_custom_field_block(self, name: str, productList: List[int] = [], cfIdList: List[int] = []) -> str:
        """
        Adds a custom field block.

        Parameters
        ----------
        name: str
            name of new custom field block
        productList: List[int]
            list of products to assign this CF; if empty list: all products
        cfIdList: List[int]
            list of CF to be shown in this block

        Returns
        -------
        str
            Id of new CF block
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Custom%20Fields/post_api_tenants__tenantId__customFields_blocks
        """
        cf_block_data: Dict[str, Union[str, List[int]]] = {'name': name}
        cf_block_data['productIds'] = productList
        cf_block_data['customFieldIds'] = cfIdList

        route = f"{self.tenant_route}/customFields/blocks"

        response = requests.post(route, json=cf_block_data, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 201, f"Add Custom Field Block failed: {response.text}"
        return response.json()['blockId']

    def patch_custom_field_block(self,
                                 blockid: str,
                                 name: str = "",
                                 productList: List[int] = [],
                                 cfIdList: List[int] = []) -> None:
        """
        Updates a custom field block.

        Parameters
        ----------
        blockId:
            id of block to update
        name: str
            name of new custom field block
        productList: List[int]
            list of products to assign this CF; if empty list: all products
        cfIdList: List[int]
            list of CF to be shown in this block

        Returns
        -------
        None
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Custom%20Fields/patch_api_tenants__tenantId__customFields_blocks__blockId_
        """
        cf_block_data: Dict[str, Union[str, List[int]]] = {}
        if name:
            cf_block_data['name'] = name
        if productList:
            cf_block_data['productIds'] = productList
        if cfIdList:
            cf_block_data['customFieldIds'] = cfIdList

        route = f"{self.tenant_route}/customFields/blocks/{blockid}"

        response = requests.patch(route, json=cf_block_data, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"Update Custom Field Block failed: {response.text}"

    def add_custom_field(self, name: str, label: str = "", type: str = "SingleLineText", default: str = "") -> int:
        """
        Add new custom field.

        Parameters
        ----------
        name: str
            name of new custom field
        label: str
            display label for custom field; if left empty, name will be used
        type: str
            custom field type; one of "Attachment", "Link", "MultiLineText", "SingleLineText" and "Toggle". 
        default: str
            default value for custom field

        Returns
        -------
        int
            Id of the custom field
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Custom%20Fields/post_api_tenants__tenantId__customFields_fields
        """
        cf_data: Dict[str, Union[str, Dict[str, str]]] = {'name': name}
        if label == "":
            label = name
        cf_data['label'] = label
        cf_data['settings'] = {'fieldType': type, 'defaultValue': default}

        route = f"{self.tenant_route}/customFields/fields"

        response = requests.post(route, json=cf_data, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 201, f"Add Custom Field failed: {response.text}"
        return response.json()['customFieldId']

    def add_test_step_block(self, product_id: str, test_case_id: str, title: str, position: int = -1) -> str:
        """
        Adds a Test Step Block in a Test Case.

        Parameters
        ----------
        product_id: str
            Id of the product

        test_case_id: str
            Id of the Test Case

        title: str
            Title of the Test Step Block

        position: int
            Position of the Test Step Block

        Returns
        -------
        str
            Id of the new Test Step Block

        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Specifications/post_api_tenants__tenantId__products__productId__specifications_testCases__testCaseId__testStepBlocks
        """
        test_block_data: Dict[str, Union[str, int]] = {'title': title}

        if position >= 0:
            test_block_data['position'] = position

        route = f"{self.__product_route(product_id)}/specifications/testCases/{test_case_id}/testStepBlocks"
        response = requests.post(route, json=test_block_data, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 201, f"Add Test Step Block failed: {response.text}"
        return str(response.json()['testStepBlockId'])

    def patch_test_step_block(self,
                              product_id: str,
                              test_case_id: str,
                              test_step_block_id: str,
                              title: str,
                              position: int = -1):
        """
        Updates a Test Step Block in a Test Case.

        Parameters
        ----------
        product_id: str
            Id of the product

        test_case_id: str
            Id of the Test Case

        test_step_block_id: str
            Id of the Test Section/Block

        title: str
            Title of the Test Step Block

        position: int
            Position of the Test Step Block

        Returns
        -------
        None

        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Specifications/patch_api_tenants__tenantId__products__productId__specifications_testCases__testCaseId__testStepBlocks__testStepBlockId_
        """
        test_block_data: Dict[str, Union[str, int]] = {'title': title}

        if position >= 0:
            test_block_data['position'] = position

        route = f"{self.__product_route(product_id)}/specifications/testCases/{test_case_id}/testStepBlocks/{test_step_block_id}"
        response = requests.patch(route, json=test_block_data, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"Patch Test Step Block failed: {response.text}"

    def remove_test_step_block(self, product_id: str, test_case_id: str, test_step_block_id: str) -> None:
        """
        Removes a Test Step Block in a Test Case.

        Parameters
        ----------
        product_id: str
            Id of the product

        test_case_id: str
            Id of the Test Case

        test_step_block_id: str
            Id of the Test Step Block

        Returns
        -------
        None

        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Specifications/delete_api_tenants__tenantId__products__productId__specifications_testCases__testCaseId__testStepBlocks__testStepBlockId_/
        """
        route = f"{self.__product_route(product_id)}/specifications/testCases/{test_case_id}/testStepBlocks/{test_step_block_id}"
        response = requests.delete(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"Remove Test Step Block failed: {response.text}"

    def add_test_step(self,
                      product_id: str,
                      test_case_id: str,
                      description: str,
                      test_block_id: str,
                      test_step_type: str = "TestStep",
                      previous_test_step_id: int = -1,
                      kwdId: str = "") -> str:
        """
        Adds a Test Step in a Test Case.

        Parameters
        ----------
        product_id: str
            Id of the product

        test_case_id: str
            Id of the Test Case

        description: str
            Description of the Test Step

        test_block_id: int
            Id of the Test Step Block

        test_step_type: str
            Type of the Test Step

        previous_test_step_id: int
            Id of the previous Test Step

        kwdId:
            Id of the Keyword

        Returns
        -------
        str
            Id of the new Test Step

        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Specifications/post_api_tenants__tenantId__products__productId__specifications_testCases__testCaseId__testSteps
        """
        test_step_data: Dict[str, Union[str, int]] = {
            'testStepType': test_step_type,
            'testStepBlockId': test_block_id,
            'description': description,
            'keywordId': kwdId,
        }

        if previous_test_step_id != -1:
            test_step_data['position'] = previous_test_step_id + 1

        route = f"{self.__product_route(product_id)}/specifications/testCases/{test_case_id}/testSteps"
        response = requests.post(route, json=test_step_data, headers=self.rest_header, verify=self.verify)

        assert response.status_code == 201, f"Add Test Step failed: {response.text}"
        return str(response.json()['testStepId'])

    def add_test_step_old(self,
                          product_id: str,
                          test_case_id: str,
                          description: str,
                          test_block_name: str = "Test",
                          previous_test_step_id: int = -1) -> str:
        """
        Adds a Test Step in a Test Case.

        Parameters
        ----------
        product_id: str
            Id of the product

        test_case_id: str
            Id of the Test Case

        description: str
            Description of the Test Step

        test_block_name: str
            Name of the Test Step Block; one of Preparation, Navigation, Test, ResultCheck or CleanUp

        previous_test_step_id: int
            Id of the previous Test Step


        Returns
        -------
        str
            Id of the new Test Step

        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Specifications/post_api_tenants__tenantId__products__productId__specifications_testCases__testCaseId__testSteps
        """
        test_step_data: Dict[str, Union[str, Dict[str, Union[str, int]]]] = {
            'testStepBlock': test_block_name,
            'description': description,
        }

        if previous_test_step_id != -1:
            test_step_data['position'] = {'relation': 'after', 'testStepId': previous_test_step_id}

        route = f"{self.__product_route(product_id)}/specifications/testCases/{test_case_id}/testSteps"
        response = requests.post(route, json=test_step_data, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 201, f"Add Test Step failed: {response.text}"
        return str(response.json()['testStepId'])

    def remove_test_step(self, product_id: str, test_case_id: str, test_step_id: str) -> None:
        """
        Removes a Test Step.

        Parameters
        ----------
        product_id: str
            Id of the product

        test_case_id: str
            Id of the Test Case

        test_step_id: str
            Id of the Test Step

        Returns
        -------
        None
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Specifications/delete_api_tenants__tenantId__products__productId__specifications_testCases__testCaseId__testSteps__testStepId_/
        """
        route = f"{self.__product_route(product_id)}/specifications/testCases/{test_case_id}/testSteps/{test_step_id}"
        response = requests.delete(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"Delete Test Step failed: {response.text}"

    def report_step_result(self, product_id: str, test_case_id: str, test_step_id: str, execution_id: str,
                           body: dict) -> None:
        """
        Reportes the result of a Test Step.

        Parameters
        ----------
        product_id: str
            Id of the product

        test_case_id: str
            Id of the Test Case

        test_step_id: str
            Id of the Test Step

        execution_id: str
            Id of the Execution

        body: dict
            Dictionary that can contain:
                - result of the Test Step (Passed, Failed, Undefined or NotApplicable)
                - comments

        Returns
        -------
        None
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/executions/openapi.yaml#/Executions/patchTestStepExecution/
        """
        route = f"{self.__product_route(product_id)}/executions/testCases/{test_case_id}/executions/{execution_id}/testSteps/{test_step_id}/v1"
        response = requests.patch(route, json=body, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 204, f"Patch Test Step result failed: {response.text}"

    def create_defect(self, product_id: str, body: dict) -> str:
        """
        Creates a defect.

        Parameters
        ----------
        product_id: str
            Id of the product

        body: dict
            Dictionary that must contain the following key:
            - name: str

        Returns
        -------
        str
            Id of the created defect
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/defects/openapi.yaml#/Defects/postDefectV1
        """
        route = f"{self.__product_route(product_id)}/defects/v1"
        response = requests.post(route, json=body, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 201, f"Create defect failed: {response.text}"
        return str(response.json()['defectId'])

    def assign_defect(self, product_id: str, body: dict) -> None:
        """
        Assigns a defect.

        Parameters
        ----------
        product_id: str
            Id of the product

        body: dict
            Dictionary that must contain the following keys:
            - parentType: str
            - parentId: str
            - defectId: int

        Returns
        -------
        None
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/defects/openapi.yaml#/Defect%20Assignments/postDefectAssignmentV1
        """
        route = f"{self.__product_route(product_id)}/defects/assignments/v1"
        response = requests.post(route, json=body, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"Assign defect failed: {response.text}"

    def get_user_story(self, product_id: str, user_story_id: str) -> dict:
        """
        Returns the content of a specific User Story.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        user_story_id: str
            Id of the User Story

        Returns
        -------
        dict
            Dictionary containing all informations of a specific User Story
            
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Requirements/get_api_tenants__tenantId__products__productId__requirements_userStories__userStoryId_/
        """
        route = f"{self.__product_route(product_id)}/requirements/userStories/{user_story_id}"
        response = requests.get(route, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"GET user Story {user_story_id} failed: {response.text}"
        return response.json()

    def post_epic(self, product_id: str, body: dict) -> str:
        """
        Creates a new Epic in TestBench CS.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        body: dict
            Dictionary that must contain the following key:
            - name: str

        Returns
        -------
        str
            Id of the new created Epic
            
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Requirements/post_api_tenants__tenantId__products__productId__requirements_epics
        """
        route = f"{self.__product_route(product_id)}/requirements/epics"
        response = requests.post(route, json=body, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 201, f"POST epic failed: {response.text}"
        return str(response.json()['epicId'])

    def patch_epic(self, product_id: str, epic_id: str, body) -> None:
        """
        Updates the content of an Epic.

        Parameters
        ----------
        product_id: str
            Id of the product

        epic_id: str
            Id of the Epic
            
        body: dict
            Dictionary with content that should be updated

        Returns
        -------
        None
        
        Notes
        -----
        For more information visit:
 
        https://test01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Requirements/patch_api_tenants__tenantId__products__productId__requirements_epics__epicId_
        """
        route = f"{self.__product_route(product_id)}/requirements/epics/{epic_id}"
        response = requests.patch(route, json=body, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"PATCH epic failed: {response.text}"

    def post_user_story(self, product_id: str, body: dict) -> str:
        """
        Creates a new User Story in TestBench CS.

        Parameters
        ----------
        product_id: str
            Id of the product
            
        body: dict
            Dictionary that must contain the following key:
            - name: str

        Returns
        -------
        str
            Id of the new created User Story
            
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Requirements/post_api_tenants__tenantId__products__productId__requirements_userStories
        """
        route = f"{self.__product_route(product_id)}/requirements/userStories"
        response = requests.post(route, json=body, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 201, f"POST user_story failed: {response.text}"
        return str(response.json()['userStoryId'])

    def patch_user_story(self, product_id: str, user_story_id: str, body) -> None:
        """
        Updates the content of a User Story.

        Parameters
        ----------
        product_id: str
            Id of the product

        user_story_id: str
            Id of the User Story
            
        body: dict
            Dictionary with content that should be updated

        Returns
        -------
        None
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/openapi-ui/?url=/doc/api.json#/Requirements/patch_api_tenants__tenantId__products__productId__requirements_userStories__userStoryId_/
        """
        route = f"{self.__product_route(product_id)}/requirements/userStories/{user_story_id}"
        response = requests.patch(route, json=body, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"PATCH user_story failed: {response.text}"

    def __gql_definition(self, variables: dict) -> str:
        """
        Transforms a list of variables into a string for graphql.

        Parameters
        ----------
        variables: dict
            Dictionary of variables

        Returns
        -------
        str
            String representation of a json like format
        """
        definition = ""
        for var in variables:
            if definition != "":
                definition = definition + ", "
            definition = definition + " " + var + " : " + "$" + var
        definition = "{" + definition + "}"

        return definition

    def __gql_signature(self, variables: dict) -> str:
        """
        Transforms a list of variables into a signature for graphql (to tell the query/mutation what variables to expect).
        
        Parameters
        ----------
        variables: dict
            Dictionary of variables

        Returns
        -------
        str
            Query variables
        """
        query_variables = ""
        if len(variables) > 0:
            for var in variables:
                if query_variables != "":
                    query_variables = query_variables + ", "
                if type(variables[var]) is int:
                    query_variables = query_variables + "$" + var + ": Int!"
                elif type(variables[var]) is float:
                    query_variables = query_variables + "$" + var + ": Float!"
                elif type(variables[var]) is bool:
                    query_variables = query_variables + "$" + var + ": Boolean!"
                else:
                    query_variables = query_variables + "$" + var + ": String!"

            query_variables = "(" + query_variables + ")"

        return query_variables

    def create_keyword(self, product_id: str, variables: Dict[str, str]) -> str:
        """
        Creates a new keyword.
        
        Parameters
        ----------
        product_id: str
            Id of the product

        variables: dict
            Dictionary of variables
            - name: str (mandatory)
            - description: str (optional)

        Returns
        -------
        str
            Id of the new created keyword
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/api/kdt/
        """
        mutation = """
        mutation""" + self.__gql_signature(variables) + """
        {
            createKeyword( ids: {
                tenantId: """ + self.tenant_id + """,
                productId: """ + product_id + """,
            },
            keyword: """ + self.__gql_definition(variables) + """)
            {
                id
            }
        }
        """

        query: Dict[str, Union[str, Dict[str, str]]] = {'query': mutation}
        query['variables'] = variables

        response = requests.post(f"{self.tbcs_base}/api/kdt/", json=query, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"MUTATION create keyword failed: {response.text}"
        return str(response.json()['data']['createKeyword']['id'])

    def update_keyword(self, product_id: str, keyword_id: str, variables: Dict[str, str]) -> str:
        """
        Updates a new keyword.
        
        Parameters
        ----------
        product_id: str
            Id of the product

        keyword_id: str
            Id of the keyword

        variables: dict
            Dictionary with content that should be updated
            - "name"          (optional)
            - "description"   (optional)
            - "originalText"  (optional)
            - "codeBlock"     (optional)
            - "status"        (optional)
            - "library"       (optional)
            - "isImplemented" (optional)

        Returns
        -------
        str
            Id of the updated keyword
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/api/kdt/
        """
        mutation = """
        mutation""" + self.__gql_signature(variables) + """
        {
            updateKeyword( ids: {
                tenantId: """ + self.tenant_id + """,
                productId: """ + product_id + """,
                keywordId: \"""" + keyword_id + """\",
             },
            keywordForUpdate: """ + self.__gql_definition(variables) + """)
            {
                _id
            }
        }
        """

        query: Dict[str, Union[str, Dict[str, str]]] = {'query': mutation}
        query['variables'] = variables

        response = requests.post(f"{self.tbcs_base}/api/kdt/", json=query, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"MUTATION update keyword failed: {response.text}"
        return str(response.json()['data']['updateKeyword']['_id'])

    def create_keyword_param(self, product_id: str, keyword_id: str, variables: Dict[str, str]) -> str:
        """
        Creates a keyword parameter.
        
        Parameters
        ----------
        product_id: str
            Id of the product

        keyword_id: str
            Id of the keyword

        variables: dict
            Dictionary with content that should be updated
            - paramName: str (mandatory)
            - paramDescription: str (optional)

        Returns
        -------
        str
            Id of the keyword parameter
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/api/kdt/
        """
        mutation = """
        mutation""" + self.__gql_signature(variables) + """
        {
            createKeywordParam( ids: {
                tenantId: """ + self.tenant_id + """,
                productId: """ + product_id + """,
                keywordId: \"""" + keyword_id + """\",
            },
            keywordParam: """ + self.__gql_definition(variables) + """)
            {
                id
            }
        }
        """

        query: Dict[str, Union[str, Dict[str, str]]] = {'query': mutation}
        query['variables'] = variables

        response = requests.post(f"{self.tbcs_base}/api/kdt/", json=query, headers=self.rest_header, verify=self.verify)
        assert response.status_code == 200, f"MUTATION create keyword parameter failed: {response.text}"
        return str(response.json()['data']['createKeywordParam']['id'])

    def get_keyword_list(self, product_id: str) -> dict:
        """
        Retrieve all keywords.
        
        Parameters
        ----------
        product_id: str
            Id of the product

        Returns
        -------
        dict
            Dictionary containing the keywords
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/api/kdt/
        """
        query = """
        {
            getKeywords(
                ids: {
                    tenantId: """ + self.tenant_id + """,
                    productId: """ + product_id + """
                }
            )     
            {
                id
                name
                description
                parameters {
                    id 
                    name
                    description
                }
                originalText
                isImplemented
            }     
        }
        """
        response = requests.post(f"{self.tbcs_base}/api/kdt/",
                                 json={'query': query},
                                 headers=self.rest_header,
                                 verify=self.verify)
        assert response.status_code == 200, f"QUERY get keyword list failed:{response.text}"
        return response.json()['data']['getKeywords']

    def get_keyword(self, product_id: str, keyword_id: str) -> dict:
        """
        Retrieve a single keyword.
        
        Parameters
        ----------
        product_id: str
            Id of the product

        keyword_id: str
            Id of the keyword

        Returns
        -------
        dict
            Dictionary containing the information of a keyword
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/api/kdt/
        """
        query = """
        {
            getKeyword(
                ids: {
                    tenantId: """ + self.tenant_id + """,
                    productId: """ + product_id + """,
                    keywordId: \"""" + keyword_id + """\"
                }
            )   {
                id 
                name
                description
                library
                parameters {
                    id
                    name
                    description
                }
                originalText
                isImplemented
            }
        }
        """
        response = requests.post(f"{self.tbcs_base}/api/kdt/",
                                 json={'query': query},
                                 headers=self.rest_header,
                                 verify=self.verify)
        assert response.status_code == 200, f"QUERY get keyword failed: {response.text}"
        return response.json()['data']['getKeyword']

    def get_keyword_parameters_and_values(self, product_id: str, test_case_id: str, step_id: str, par_id: str) -> str:
        """
        Retrieve the keyword value of a specific parameter.
        
        Parameters
        ----------
        product_id: str
            Id of the product

        test_case_id: str
            Id of the Test Case

        step_id: str
            Id of the Test Step
        
        par_id:
            Id of the parameter

        Returns
        -------
        str
            Value of the keyword parameter
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/api/kdt/
        """
        query = """
        {
            getKeywordParametersAndValues(
                ids: {
                    tenantId: """ + self.tenant_id + """,
                    productId: """ + product_id + """,
                    testCaseId: """ + test_case_id + """,
                    testStepId: """ + step_id + """,
                    paramId: \"""" + par_id + """\"
                }
            )   {
                value
            }
        }
        """
        response = requests.post(f"{self.tbcs_base}/api/kdt/",
                                 json={'query': query},
                                 headers=self.rest_header,
                                 verify=self.verify)
        assert response.status_code == 200, f"QUERY get keyword failed: {response.text}"
        return response.json()['data']['getKeywordParametersAndValues']['value']

    def delete_keyword(self, product_id: str, keyword_id: str) -> str:
        """
        Delete a specific keyword.
        
        Parameters
        ----------
        product_id: str
            Id of the product

        keyword_id: str
            Id of the keyword

        Returns
        -------
        str
            Id of the deleted keyword
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/api/kdt/
        """
        mutation = """
        mutation
        {
            deleteKeyword(
                ids: {
                    tenantId: """ + self.tenant_id + """,
                    productId: """ + product_id + """,
                    keywordId: \"""" + keyword_id + """\"
                }
            )   
            {
                _id    
            }
        }
        """
        response = requests.post(f"{self.tbcs_base}/api/kdt/",
                                 json={'query': mutation},
                                 headers=self.rest_header,
                                 verify=self.verify)
        assert response.status_code == 200, f"MUTATION delete keyword failed: {response.text}"
        return response.json()['data']['deleteKeyword']

    def add_keyword_usage(self, product_id: str, epic_id: str, user_story_id: str, test_case_id: str, test_step_Id: str,
                          keyword_id: str) -> dict:
        """
        Adds to a keyword where it is used
        
        Parameters
        ----------
        product_id: str
            Id of the product

        epic_id: str
            Id of the epic

        user_story_id: str
            Id of the User Story

        test_case_id: str
            Id of the Test Case

        test_step_id: str
            Id of the Test Step

        keyword_id: str
            Id of the keyword

        Returns
        -------
        dict
            Dictionary of the usage parameters
        
        Notes
        -----
        For more information visit:
 
        https://cloud01-eu.testbench.com/api/kdt/
        """
        optional_ids = ""
        if int(epic_id) > 0:
            optional_ids = "\n epicId: " + epic_id + ", "
        if int(user_story_id) > 0:
            optional_ids = optional_ids + "\n userStoryId: " + user_story_id + ", "

        mutation = """
        mutation
        {
            addKeywordUsage(
                ids: {
                    tenantId: """ + self.tenant_id + """,
                    productId: """ + product_id + """, 
                    keywordId: \"""" + keyword_id + """\"
                },                
                
                keywordUsageParams: { """ + optional_ids + """
                    testCaseId: """ + test_case_id + """,
                    testStepId: """ + test_step_Id + """
                }
            )   
            {
                keywordId   
            }
        }
        """

        response = requests.post(f"{self.tbcs_base}/api/kdt/",
                                 json={'query': mutation},
                                 headers=self.rest_header,
                                 verify=self.verify)
        assert response.status_code == 200, f"MUTATION add keyword usage failed: {response.text}"
        return response.json()['data']['addKeywordUsage']

    def update_kwd_par_value(self, product_id: str, test_case_id: str, test_step_id: str, parameter_id: str,
                             value: str) -> str:
        """
            Adds or updates a value for a Keyword parameter in a test sequence
            
            Parameters
            ----------
            product_id: str
                Id of the product

            test_case_id: str
                Id of the Test Case

            test_step_id: str
                Id of the Test Step

            parameter_id: str
                Id of the parameter

            value: str
                New value for the parameter in this instance of the Keyword

            Returns
            -------
            str
                Value of the parameter on success
            
            Notes
            -----
            For more information visit:
    
            https://cloud01-eu.testbench.com/api/kdt/
            """

        mutation = """
            mutation
            {
                upsertKeywordParamValue(
                    ids: {
                        tenantId: """ + self.tenant_id + """,
                        productId: """ + product_id + """, 
                        testCaseId: """ + test_case_id + """,
                        testStepId: """ + test_step_id + """,
                        paramId: \"""" + parameter_id + """\",
                    },                
                    
                    paramValue: {  
                        text: \"""" + value + """\",
                        
                    }
                )   
                {
                    paramValue   
                }
            }
            """

        response = requests.post(f"{self.tbcs_base}/api/kdt/",
                                 json={'query': mutation},
                                 headers=self.rest_header,
                                 verify=self.verify)
        assert response.status_code == 200, f"MUTATION upsert Keyword Param Value failed: {response.text}"
        return response.json()['data']['upsertKeywordParamValue']['paramValue']
