import argparse
import ast
import os
import re
from typing import Dict, Union

from robot.api import get_model

import config
import utils.logger_utils as logger_utils
import utils.tbcs_utils as tbcs_utils
from utils.terminal_utils import ProgressIndicator


class TestSuiteParser(ast.NodeVisitor):

    test_cases = []
    keywords = []
    test_setup = []
    test_teardown = []
    tc_counter = -1
    kwd_counter = -1
    test_case = True

    def visit_TestCaseName(self, node):
        self.test_cases.append({'TestCaseName': node.name, 'TestSteps': [], 'Tags': [], 'Description': []})
        self.tc_counter += 1
        self.test_case = True

    def visit_KeywordName(self, node):
        self.keywords.append({
            'KeywordName': node.name,
            'Arguments': [],
            'TestSteps': [],
            'Tags': [],
            'Description': [],
            'Codeblock': ""
        })
        self.kwd_counter += 1
        self.test_case = False

    def visit_KeywordCall(self, node):
        args = '    '.join(node.args)
        if self.test_case:
            self.test_cases[self.tc_counter]['TestSteps'].append(node.keyword + '    ' + args)
        else:
            self.keywords[self.kwd_counter]['TestSteps'].append(node.keyword + '    ' + args)

    def visit_TestSetup(self, node):
        args = '    '.join(node.args)
        self.test_setup.append(node.name + '    ' + args)

    def visit_TestTeardown(self, node):
        args = '    '.join(node.args)
        self.test_teardown.append(node.name + '    ' + args)

    def visit_Tags(self, node):
        for value in node.values:
            if value[0:3] == 'ID:':
                self.test_cases[self.tc_counter]['Tags'].append(value[3:])

    def visit_Arguments(self, node):
        if not self.test_case:
            for value in node.values:
                self.keywords[self.kwd_counter]['Arguments'].append({'name': value[2:-1]})

    def visit_Documentation(self, node):
        if self.test_case:
            self.test_cases[self.tc_counter]['Description'].append(node.value)
        else:
            self.keywords[self.kwd_counter]['Description'].append(node.value)


def add_test_steps(test_block_steps, test_block_id, keyword_ids):
    if test_block_steps:
        for count, test_step in enumerate(test_block_steps):
            if config.TEST_STEP_TYPE == "Keyword":
                test_step_id = tbcs.add_test_step(product_id, test_case_id, test_step, test_block_id, "keyword", count,
                                                  keyword_ids[count]['id'])

                for parameter in keyword_ids[count]['par_list']:
                    tbcs.update_kwd_par_value(product_id, test_case_id, test_step_id, parameter['id'],
                                              parameter['value'])
            else:
                tbcs.add_test_step(product_id, test_case_id, test_step, test_block_id, "TestStep", count)


def check_for_update(robot_test_block, tbcs_test_case_item, tbcs_test_block, test_block_name):
    test_case_id = str(tbcs_test_case_item['id'])

    if not tbcs_test_block:
        tbcs.add_test_step_block(product_id, test_case_id, test_block_name, -1)
        return True

    if len(robot_test_block) != len(tbcs_test_block['steps']):
        return True

    for count, item1 in enumerate(robot_test_block):
        item2 = tbcs_test_block['steps'][count]
        if item1 != item2['description']:
            return True

    return False


def create_and_update_keywords(test_step_block):
    test_step_ids = []
    for test_step in test_step_block:
        parameters = re.split(r"\s{2,}", test_step)
        keyword_name = parameters.pop(0)

        par_list = []
        for count, parameter in enumerate(parameters):
            par_list.append({'name': f"param{count}"})

        keyword_params = {
            'name': keyword_name,
            'parlist': par_list,
            'description': "",
        }

        for keyword in robotParser.keywords:
            if keyword_name == keyword['KeywordName']:
                keyword_params['description'] = keyword['Description'][0][:3998]

        keyword_ids = tbcs_utils.get_or_create_kwd(
            logger,
            tbcs,
            product_id,
            keyword_params,
        )

        # Update parameter values
        for count, parameter in enumerate(parameters):
            keyword_ids['par_list'][count]['value'] = parameter

        # After creation, update Keyword with those details we cannot provide while creating
        keyword_params = {}

        keyword_params["library"] = "resource:" + os.path.basename(file)
        keyword_params["isImplemented"] = True

        tbcs.update_keyword(product_id, keyword_ids['id'], keyword_params)
        test_step_ids.append(keyword_ids)

    return test_step_ids


if __name__ == "__main__":
    # Configure logging
    logger = logger_utils.get_logger("Import_tc_rf", config.LOGLEVEL)

    # Parse command line
    argsParser = argparse.ArgumentParser(description="Import Robot Framework Test Case.")
    argsParser.add_argument("source",
                            nargs="+",
                            default=[''],
                            help='name of one or more files or folders to be scanned')
    argsParser.add_argument('-tc',
                            '--testcase',
                            nargs="+",
                            default=[''],
                            help='name of one or more Test Cases to be imported')

    plist = tbcs_utils.handle_default_args(config.ACCOUNT, argsParser)

    files = tbcs_utils.get_files(logger, plist.source)
    if len(files) == 0:
        logger.error('No files found for scanning. Skipping ...')
        exit(1)

    # connect to iTB and select product to write in (for simplicity: 1st product in list)
    tbcs = tbcs_utils.connect_itb(logger, config.ACCOUNT)

    logger.info("Connected to ITB")

    product_id = tbcs_utils.ask_for_product(logger, tbcs)

    if not product_id:
        exit(1)

    # Create adapter custom field in TestBench CS
    custom_field = tbcs_utils.get_or_create_CF(
        logger,
        tbcs,
        [config.ADAPTER_CUSTOM_FIELD_NAME],
        "Automation Test Case",
        "TestCase",
        "BeforeAutomation",
    )

    progress_bar_files = ProgressIndicator(len(files), 'Scanning', 'Files')

    for file in files:
        if not file.endswith(".robot"):
            continue

        logger.info(f"Visit the following robot file: {file}")
        # Parse Test Suite and retrieve information
        model = get_model(file)
        robotParser = TestSuiteParser()
        robotParser.visit(model)
        logger.info(f"Test Setup: {robotParser.test_setup}")
        logger.info(f"Test Teardown: {robotParser.test_teardown}")

        if plist.testcase != ['']:
            progress_bar_tests = ProgressIndicator(len(plist.testcase), 'Scanning', 'Test Cases')
        else:
            progress_bar_tests = ProgressIndicator(len(robotParser.test_cases), 'Scanning', 'Test Cases')

        for test_case in robotParser.test_cases:
            test_case_name = test_case['TestCaseName']
            if plist.testcase != None and plist.testcase != ['']:
                if not test_case_name in plist.testcase:
                    logger.debug(f"Skipped Test Case: {test_case_name}")
                    continue

            logger.info(f"Check Test Case '{test_case_name}'")
            tbcs_test_case = tbcs.get_test_case_by_filter(product_id, 'title', 'equals', test_case_name)

            needs_update = {'Setup': True, 'TestSteps': True, 'Teardown': True}

            if not tbcs_test_case:  # Test Case doesn't exist
                logger.info(f"Test Case '{test_case_name}' doesn't exist")
                test_case_id = tbcs.post_test_case(product_id, {
                    'name': test_case_name,
                    'testCaseType': 'StructuredTestCase',
                    "customTestSequenceTitles": []
                })

                test_block_setup = {'id': tbcs.add_test_step_block(product_id, test_case_id, "Setup")}
                test_block_test_steps = {'id': tbcs.add_test_step_block(product_id, test_case_id, "Test Steps")}
                test_block_teardown = {'id': tbcs.add_test_step_block(product_id, test_case_id, "Teardown")}

                tbcs_test_case_item = tbcs.get_test_case(product_id, test_case_id)

            else:
                logger.info(f"Test Case '{test_case_name}' already exists")
                if len(tbcs_test_case) > 1:  # Found more than 1 Test Case
                    logger.warning(
                        "2 or more Test Cases share the same name in TestBench CS. Updates only the first one found.")

                test_case_id = str(tbcs_test_case[0]['id'])
                tbcs_test_case_item = tbcs.get_test_case(product_id, test_case_id)

                test_block_setup = tbcs_utils.get_test_step_block(logger, tbcs, tbcs_test_case_item, "Setup")
                test_block_test_steps = tbcs_utils.get_test_step_block(logger, tbcs, tbcs_test_case_item, "Test Steps")
                test_block_teardown = tbcs_utils.get_test_step_block(logger, tbcs, tbcs_test_case_item, "Teardown")

                # Check if Test Case needs update
                needs_update['Setup'] = check_for_update(robotParser.test_setup, tbcs_test_case_item, test_block_setup,
                                                         "Setup")

                needs_update['TestSteps'] = check_for_update(test_case['TestSteps'], tbcs_test_case_item,
                                                             test_block_test_steps, "Test Steps")

                needs_update['Teardown'] = check_for_update(robotParser.test_teardown, tbcs_test_case_item,
                                                            test_block_teardown, "Teardown")

            # Update Test Step Blocks
            if needs_update['Setup'] or needs_update['TestSteps'] or needs_update['Teardown']:
                logger.info(f"Test Case '{test_case_name}' needs an update")
            else:
                logger.info(f"Test Case '{test_case_name}' doesn't need an update")

            if needs_update['Setup']:
                if test_block_setup:
                    tbcs.remove_test_step_block(product_id, test_case_id, str(test_block_setup['id']))

                test_block_id = tbcs.add_test_step_block(product_id, test_case_id, "Setup", -1)

                if config.TEST_STEP_TYPE == "Keyword":
                    setup_keyword_ids = create_and_update_keywords(robotParser.test_setup)
                else:
                    setup_keyword_ids = []

                add_test_steps(robotParser.test_setup, test_block_id, setup_keyword_ids)

            if needs_update['TestSteps']:
                if test_block_test_steps:
                    tbcs.remove_test_step_block(product_id, test_case_id, str(test_block_test_steps['id']))

                test_block_id = tbcs.add_test_step_block(product_id, test_case_id, "Test Steps", -1)

                if config.TEST_STEP_TYPE == "Keyword":
                    test_steps_keyword_ids = create_and_update_keywords(test_case['TestSteps'])

                else:
                    test_steps_keyword_ids = []

                add_test_steps(test_case['TestSteps'], test_block_id, test_steps_keyword_ids)

            if needs_update['Teardown']:
                if test_block_teardown:
                    tbcs.remove_test_step_block(product_id, test_case_id, str(test_block_teardown['id']))

                test_block_id = tbcs.add_test_step_block(product_id, test_case_id, "Teardown", -1)

                if config.TEST_STEP_TYPE == "Keyword":
                    teardown_keyword_ids = create_and_update_keywords(robotParser.test_teardown)
                else:
                    teardown_keyword_ids = []

                add_test_steps(robotParser.test_teardown, test_block_id, teardown_keyword_ids)

            # Patch TBCS Test Case
            patchBody: Dict[str, Union[bool, dict, list]] = {
                "isAutomated": True,
                "toBeReviewed": True,
            }

            if test_case['Tags']:
                patchBody['externalId'] = {"value": test_case['Tags'][0]}
                logger.info("Updating external ID in TBCS")

            # Update description
            if test_case['Description']:
                patchBody['description'] = {"text": test_case['Description'][0]}
                logger.info("Updating description in TBCS")

            # Set Test Tool custom field
            if custom_field:
                patchBody['customFields'] = [{
                    "customFieldId": custom_field[config.ADAPTER_CUSTOM_FIELD_NAME.upper()],
                    "value": "RobotFramework"
                }]

            tbcs.patch_test_case(product_id, test_case_id, patchBody)
            progress_bar_tests.update_progress(test_case_name)

        progress_bar_files.update_progress(file)
