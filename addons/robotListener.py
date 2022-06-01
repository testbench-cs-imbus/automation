#
# Listener for Robot Framework
#

import os
import sys

# include agent and tbcsApi from base dir (cwd)
sys.path.insert(0, os.getcwd())

import json
import logging
import os
from tempfile import TemporaryDirectory

import config
import utils.comparison_utils as comparison_utils
import utils.logger_utils as logger_utils
from utils.tbcs_api import TbcsApi


class robotListener:
    ROBOT_LISTENER_API_VERSION = 2

    logger: logging.Logger
    tbcs: TbcsApi
    test_case_item: dict
    product_id: str
    test_case_id: str
    external_id: str
    temp_dir: TemporaryDirectory

    execution_id: str
    skip: bool

    test_steps = []

    def __init__(self, tbcs_base, tenant_id, user_id, session_token, verify, test_case_item, execution_id):
        self.tbcs = TbcsApi(tbcs_base, tenant_id, user_id, session_token)
        self.tbcs.verify = comparison_utils.stringToBoolean(verify)  #type: ignore

        # for debugging on local setups -->
        import urllib3

        if verify == "False":
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  #type: ignore

        self.test_case_item = json.loads(test_case_item)
        self.product_id = str(self.test_case_item['productId'])
        self.test_case_id = str(self.test_case_item['id'])
        self.external_id = str(self.test_case_item['automation']['externalId'], )
        self.execution_id = execution_id
        self.skip = False

        self.logger = logger_utils.get_logger(self.__class__.__name__ + "_" + self.execution_id, config.LOGLEVEL)
        self.logger.info("Initialize Listener")

    def start_test(self, name, attributes):
        self.logger.info("Start Test Case with name: " + name)

        # Retrieve Test Steps from TBCS
        for test_step_block in self.test_case_item['testSequence']['testStepBlocks']:
            self.test_steps.extend([step for step in test_step_block['steps']])

    def start_keyword(self, name, attributes):
        # Check if keyword matches Test Step in TBCS

        if comparison_utils.is_equal_ignore_separators(self.test_steps[0]['description'].split("  ")[0],
                                                       attributes['kwname']):
            self.skip = True

    def end_keyword(self, name, attributes):
        # Check if keyword matches Test Step in TBCS
        if comparison_utils.is_equal_ignore_separators(self.test_steps[0]['description'].split("  ")[0],
                                                       attributes['kwname']):
            self.skip = False

        # Skip all level-2 layer keywords
        if self.skip:
            return

        if attributes['status'] == "PASS":
            result = "Passed"
        elif attributes['status'] == "FAIL":
            result = "Failed"
        else:
            result = "Undefined"

        self.tbcs.report_step_result(self.product_id, self.test_case_id, self.test_steps[0]['id'], self.execution_id,
                                     {"result": result})

        # Remove reported Test Step from Stack
        self.test_steps.pop(0)

    def log_message(self, message):
        if message['level'] == "FAIL" and config.CREATE_DEFECTS:
            test_step_name = self.test_steps[0]['description']
            defect_create_body = {
                "name": f'Execution {self.execution_id} - {test_step_name}',
                "description": message['message']
            }

            defect_id: str = self.tbcs.create_defect(self.product_id, defect_create_body)

            defect_assign_body = {
                "defectId": defect_id,
                "parentType": "TestStep",
                "parentId": f'{self.test_case_id}-{self.execution_id}-{self.test_steps[0]["id"]}'
            }
            self.tbcs.assign_defect(self.product_id, defect_assign_body)

            self.logger.error("Test Step with ID: " + str(self.test_steps[0]["id"]) + " and name: " +
                              self.test_steps[0]["description"] + " failed!")
