#
# Adapter for Behave
# https://behave.readthedocs.io/en/stable/index.html
#

import json
import os
import subprocess
from pathlib import Path

import config
import utils.comparison_utils as comparison_utils
import utils.logger_utils as logger_utils
from utils.tbcs_api import TbcsApi


class Behave:

    product_id: str
    test_case_id: str
    execution_id: str

    def __init__(self, tbcs, concrete_test_case, abstract_test_case, execution_id, temp_dir):
        self.product_id = str(concrete_test_case['productId'])
        self.test_case_id = str(concrete_test_case['id'])
        self.execution_id = execution_id

        self.__tbcs: TbcsApi = tbcs
        self.__concrete_test_case = concrete_test_case
        self.__abstract_test_case = abstract_test_case
        self.__test_case_name = concrete_test_case['name']

        # Create logger
        self.__logger = logger_utils.get_logger(self.__class__.__name__ + "_" + self.execution_id, config.LOGLEVEL)

        # Save folder paths
        self.__scenario_dir = str(Path(config.BEHAVE['base_dir'] + config.BEHAVE['scenario_dir'])).replace("\\", "/")
        self.__result_dir = str(Path(config.BEHAVE['base_dir'] + config.BEHAVE['result_dir'])).replace("\\", "/")

        # Define feature file name
        self.__featureFileName = self.__scenario_dir + \
            "/" + self.__test_case_name + ".feature"

        # Create folder for created files, if it doesn't exist
        Path(self.__scenario_dir).mkdir(parents=True, exist_ok=True)

        # Create result folder, if it doesn't exist
        Path(self.__result_dir).mkdir(parents=True, exist_ok=True)

        self.__logger.info("Adapter initialized")

    def execute_test_case(self, parallel, ddt_row):

        if self.__abstract_test_case["testCaseType"] != 'StructuredTestCase':
            self.__logger.error("Only structured test cases can be used for test automation. TC '" +
                                self.__abstract_test_case["name"] + "' is of type: " +
                                self.__abstract_test_case["testCaseType"])
            exit(-1)

        # Prepare name of Test Case - resolve varaibles, if any.
        self.__logger.info("Name of Test Case: " + self.__test_case_name)

        # Create feature file
        self.__logger.info("creating scenario file: " + self.__featureFileName)
        scFile = open(self.__featureFileName, "w", encoding="utf-8")

        # For feature name use name of parent user story, if test case has one.
        feature_name = ""
        if "userStoryId" in self.__abstract_test_case:
            userStoryId = self.__abstract_test_case['userStoryId']
            if userStoryId != None:
                user_story = self.__tbcs.get_user_story(self.product_id, userStoryId)
                feature_name = user_story['name']
        if feature_name == "":
            feature_name = "generic"

        scFile.write("Feature: " + feature_name + "\n\n")
        scFile.write("  Scenario: " + self.__test_case_name + "\n")

        for blocks in self.__concrete_test_case["testSequence"]["testStepBlocks"]:
            if len(blocks["steps"]) > 0:
                first = True
                for count in range(0, len(blocks["steps"])):
                    step = blocks["steps"][count]

                    if first:
                        if comparison_utils.is_equal_ignore_separators(
                                blocks["title"], "Preparation") or comparison_utils.is_equal_ignore_separators(
                                    blocks["title"], "Given"):
                            scFile.write("    Given ")
                        elif comparison_utils.is_equal_ignore_separators(
                                blocks["title"], "Test") or comparison_utils.is_equal_ignore_separators(
                                    blocks["title"], "When"):
                            scFile.write("     When ")
                        elif comparison_utils.is_equal_ignore_separators(
                                blocks["title"], "ResultCheck") or comparison_utils.is_equal_ignore_separators(
                                    blocks["title"], "Then"):
                            scFile.write("     Then ")
                        else:
                            scFile.write("      And ")
                    else:
                        scFile.write("      And ")

                    first = False

                    if step["testStepType"] == "TestStep":
                        scFile.write(step["description"] + "\n")
                        step['stepOutput'] = step["description"]
                    if step["testStepType"] == "Keyword":
                        kwd = self.__tbcs.get_keyword(self.product_id, step['keywordId'])

                        if kwd != None:
                            kwd_text = kwd['name']
                            if step['keyword'] != None:  #  DDT
                                parameters = step['keyword']['parameters']
                                for par in parameters:
                                    kwd_text = kwd_text.replace('{' + par['name'] + '}', par['value'])
                            else:
                                for par in kwd['parameters']:  # NOT DDT
                                    value = self.__tbcs.get_keyword_parameters_and_values(
                                        self.product_id, self.test_case_id, str(step['id']), str(par['id']))
                                    kwd_text = kwd_text.replace('{' + par['name'] + '}', value)

                            step['stepOutput'] = kwd_text

                        scFile.write(kwd_text + "\n")

        scFile.close()

        self.__resultFile = self.__result_dir + "/" + self.__test_case_name + ".json"
        call = ["behave", "-o", self.__resultFile]

        # Select output and test case to run
        call.extend(["--format=json.pretty"])
        call.extend([self.__featureFileName])

        self.__logger.debug(call)

        try:
            if parallel:
                # Call to execute behave cases parallel
                result = subprocess.Popen(call)
            else:
                # Call to execute behave test cases sequential
                result = subprocess.run(call)

        except Exception as e:
            self.__logger.error(f"Subprocess method failed!\n\t{e.__str__()}")
            return None

        return result

    def check_result(self, executed_cmd):
        # Check if behave call failed
        returncode = executed_cmd['subprocess_instance'].returncode

        # read result file
        try:
            self.__tbcs.upload_file_to_execution(self.product_id, self.test_case_id, self.execution_id,
                                                 self.__resultFile)

            with open(self.__resultFile, 'r') as file:
                obj = json.load(file)

            myScenario = {}
            verdict = "open"
            for features in obj:
                if "elements" in features:
                    for scenarios in features["elements"]:
                        if scenarios["name"] == self.__test_case_name:
                            verdict = scenarios["status"]
                            myScenario = scenarios

            if verdict != "open":
                # try to associate steps in TestBench with steps in behave result file - normally, that should work 1:1
                stepCount = 0
                for blocks in self.__concrete_test_case["testSequence"]["testStepBlocks"]:
                    if len(blocks["steps"]) > 0:
                        for count in range(0, len(blocks["steps"])):
                            step = blocks["steps"][count]

                            gherkinStep = myScenario["steps"][stepCount]
                            # just to make sure: is this really the same step?
                            if gherkinStep["name"] == step['stepOutput']:
                                # if a step fails, the following steps will not receive a result - thus it could be missing
                                if "result" in gherkinStep:
                                    if gherkinStep["result"]["status"] == "passed":
                                        self.__tbcs.report_step_result(self.product_id, self.test_case_id, step['id'],
                                                                       self.execution_id, {"result": "Passed"})
                                    if gherkinStep["result"]["status"] == "failed":
                                        self.__tbcs.report_step_result(self.product_id, self.test_case_id, step['id'],
                                                                       self.execution_id, {"result": "Failed"})

                            stepCount = stepCount + 1

            if config.BEHAVE["cleanup"]:
                os.remove(self.__featureFileName)
        except Exception as e:
            self.__logger.error(f"Failed to import result!\n\t{e.__str__()}")
            self.__logger.debug(
                f"\n\t{e.__str__()}\n\tIn: {e.__traceback__.tb_frame.f_code}\n\tAt Line: {e.__traceback__.tb_lineno}"
            )  # pyright: reportOptionalMemberAccess=false
            return "Failed"

        if verdict == "failed" or returncode > 0:
            return "Failed"
        else:
            return "Passed"

    # This method is called after all tests are executed.
    def final_cleanup(self):
        self.__logger.info('Final cleanup')
        # Do some adapter specific cleanup

        # remove logger instances (save memory)
        logger_utils.remove_logger(self.__logger.name)
        pass
