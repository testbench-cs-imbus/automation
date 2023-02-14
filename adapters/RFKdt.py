#
# Adapter for Robot Framework KDT
# https://robotframework.org/
#

import json
import subprocess
from glob import glob
from pathlib import Path
from shutil import rmtree

import config
import utils.comparison_utils as comparison_utils
import utils.logger_utils as logger_utils

from adapters.AdapterTemplate import AdapterTemplate


class RFKdt(AdapterTemplate):

    product_id: str
    test_case_id: str
    execution_id: str

    def __init__(self, tbcs, concrete_test_case, abstract_test_case, execution_id, temp_dir):
        self.product_id = str(concrete_test_case['productId'])
        self.test_case_id = str(concrete_test_case['id'])
        self.execution_id = execution_id

        self.__tbcs = tbcs
        self.__concrete_test_case = concrete_test_case
        self.__abstract_test_case = abstract_test_case
        self.__test_case_name = concrete_test_case['name']
        self.__external_id = concrete_test_case['automation']['externalId']

        # Avoid Winerror 206
        self.__concrete_test_case['executions'] = self.__abstract_test_case['executions'] = ""

        # Create logger
        self.__logger = logger_utils.get_logger(self.__class__.__name__ + "_" + self.execution_id, config.LOGLEVEL)
        # Save folder paths
        self.__script_dir = str(Path(config.ROBOT_KDT['base_dir'] + config.ROBOT_KDT['script_dir']).absolute()).replace(
            "\\", "/")
        # Make sure that a path or similar in a TC name does not cause trouble later when writing files based on TC name
        self.__test_case_name = "".join(x if (x.isalnum() or x in "._- ") else "_" for x in self.__test_case_name)

        self.__result_dir = str(
            Path(config.ROBOT_KDT['base_dir'] + config.ROBOT_KDT['result_dir'] + "/" +
                 self.__test_case_name).absolute()).replace("\\", "/")
        self.__resource_dir = str(Path(config.ROBOT_KDT['base_dir'] +
                                       config.ROBOT_KDT['resource_dir']).absolute()).replace("\\", "/")

        # Create folder for created files, if it doesn't exist
        Path(self.__script_dir).mkdir(parents=True, exist_ok=True)

        # Create result folder, if it doesn't exist
        Path(self.__result_dir).mkdir(parents=True, exist_ok=True)

        # Create resource folder, if it doesn't exist
        Path(self.__resource_dir).mkdir(parents=True, exist_ok=True)

        self.__logger.info("Adapter initialized")

    def execute_test_case(self, parallel, ddt_row):

        if self.__abstract_test_case["testCaseType"] != 'StructuredTestCase':
            self.__logger.error("Only structured test cases can be used for test automation. TC '" +
                                self.__abstract_test_case["name"] + "' is of type: " +
                                self.__abstract_test_case["testCaseType"])
            exit(-1)

        # create list of resources/libraries to include; temporary solution! TODO: adapt to real Keywords which have lib=resource as aproperty
        # temporarily we pretend that the structure is KEYWORD%%RESOURCE
        # TODO: figure out if we need to include libraries AND resources
        lib = []
        res = []
        self.__logger.debug("Starting execution ...")

        for blocks in self.__abstract_test_case['testSequence']['testStepBlocks']:
            self.__logger.debug("entering block: " + blocks["title"])

            for steps in blocks['steps']:
                self.__logger.debug("step: " + steps["description"])

                rawLibOrRes = ""
                parts = []
                if steps['testStepType'] == 'Keyword':
                    kwd = self.__tbcs.get_keyword(self.product_id, steps['keywordId'])

                    if kwd != None:
                        rawLibOrRes = kwd['library']
                        steps['description'] = kwd[
                            'name']  # use 'description' attribute to store Keyword text fitting RF purpose
                        for par in kwd['parameters']:
                            value = self.__tbcs.get_keyword_parameters_and_values(self.product_id, self.test_case_id,
                                                                                  str(steps['id']), str(par['id']))
                            if value != "" and value != config.ROBOT_KDT[
                                    "empty_string"]:  # use named arguments syntax, omit args with empty values
                                steps['description'] = steps['description'] + "    " + par['name'] + "=" + value
                            elif value == config.ROBOT_KDT[
                                    "empty_string"]:  # empty values are possible via defined string
                                steps['description'] = steps['description'] + "    " + par['name'] + "="

                    else:
                        self.__logger.error("Keyword not found (maybe it was deleted?): " + steps['description'])
                else:
                    composed = steps['description'].split("  ")[0]
                    parts = composed.split("%%")

                    if len(parts) > 1:
                        steps['description'] = steps['description'].replace(composed, parts[0])
                        rawLibOrRes = parts[1]

                if rawLibOrRes != "":
                    if len(rawLibOrRes.split(":", 1)) > 1:
                        prefix = rawLibOrRes.split(":", 1)[0]
                        libOrRes = rawLibOrRes.split(":", 1)[1]
                    else:
                        prefix = "none"
                        libOrRes = rawLibOrRes

                    self.__logger.debug(prefix + " <-> " + libOrRes)

                    if prefix in "library":
                        if not (libOrRes in lib):
                            lib.append(libOrRes)
                    elif prefix in "resource":
                        if not (libOrRes in res):
                            res.append(libOrRes)
                    else:  # no prefix recognizable? default: keyword is from resource
                        if not (libOrRes in res):
                            res.append(libOrRes)

        self.__logger.info("Name of Test Case: " + self.__test_case_name)

        # Create robot file
        robotFile = open(self.__script_dir + "/" + self.__test_case_name + ".robot", "w", encoding="utf-8")

        if len(lib) > 0 or len(res) > 0:
            robotFile.write("*** Settings ***\n")

        if len(lib) > 0:
            for item in lib:
                robotFile.write("Library    " + item + "\n")
            robotFile.write("\n")

        if len(res) > 0:
            for item in res:
                robotFile.write("Resource    " + self.__resource_dir + "/" + item + "\n")
            robotFile.write("\n")

        if ddt_row:
            robotFile.write("*** Variables ***\n")
            for ddt_item in ddt_row:
                robotFile.write("${" + ddt_item['column'] + "}    " + ddt_item['value'] + "\n")
            robotFile.write("\n")

        robotFile.write("*** Test Cases ***\n" + self.__test_case_name + "\n\t")

        for blocks in self.__abstract_test_case["testSequence"]["testStepBlocks"]:
            if len(blocks["steps"]) > 0:
                robotFile.write("#    " + blocks["title"] + "\n\t")
                if comparison_utils.is_equal_ignore_separators(
                        blocks["title"], "Reset Environment") or comparison_utils.is_equal_ignore_separators(
                            blocks["title"], "Teardown") or comparison_utils.is_equal_ignore_separators(
                                blocks["title"], "Cleanup"):
                    robotFile.write("[Teardown]    ")
                    # RF cannot have more than one Keywords in Teardown; "Run Keywords" can be used to cluster them if more than one.
                    if len(blocks["steps"]) > 1:
                        robotFile.write("Run Keywords    ")
                if comparison_utils.is_equal_ignore_separators(
                        blocks["title"], "Preparation") or comparison_utils.is_equal_ignore_separators(
                            blocks["title"], "Setup"):
                    robotFile.write("[Setup]    ")
                    # RF cannot have more than one Keywords in Setup; "Run Keywords" can be used to cluster them if more than one.
                    if len(blocks["steps"]) > 1:
                        robotFile.write("Run Keywords    ")
                for count in range(0, len(blocks["steps"])):
                    step = blocks["steps"][count]

                    if comparison_utils.is_equal_ignore_separators(
                            blocks["title"], "Reset Environment") or comparison_utils.is_equal_ignore_separators(
                                blocks["title"], "Teardown") or comparison_utils.is_equal_ignore_separators(
                                    blocks["title"], "Cleanup") or comparison_utils.is_equal_ignore_separators(
                                        blocks["title"], "Preparation") or comparison_utils.is_equal_ignore_separators(
                                            blocks["title"], "Setup"):
                        robotFile.write(step["description"])
                        if count < len(blocks["steps"]) - 1:
                            robotFile.write("    AND\n    ...    ")
                        else:
                            robotFile.write("\n\t")
                    else:
                        robotFile.write(step["description"] + "\n\t")

        robotFile.close()

        call = ["python", "-m", "robot", "--outputdir", self.__result_dir]

        if self.__external_id:
            # Use external_id for Test Case selection
            call.extend(["-i", "ID:" + self.__external_id])
        else:
            # Use Test Case name for selection
            call.extend(["-t", self.__test_case_name])

        call.extend([
            "--listener", "./addons/robotListener.py;" + str(self.__tbcs.tbcs_base) + ";" + str(self.__tbcs.tenant_id) +
            ";" + str(self.__tbcs.user_id) + ";" + str(self.__tbcs.session_token) + ";" + str(self.__tbcs.verify) +
            ";" + json.dumps(self.__abstract_test_case) + ";" + self.execution_id
        ])

        call.extend([
            "--log", self.__test_case_name + "-log.html", "--report", self.__test_case_name + "-report.html",
            "--output", self.__test_case_name + "-output.xml", self.__script_dir
        ])

        try:
            if parallel:
                # Call to execute robot framework test cases parallel
                result = subprocess.Popen(call)
            else:
                # Call to execute robot framework test cases sequential
                result = subprocess.run(call)

        except Exception as e:
            self.__logger.error(f"Subprocess method failed!\n\t{e.__str__()}")
            return None

        return result

    def check_result(self, executed_cmd):
        if config.ROBOT_KDT['cleanup']:
            Path(self.__script_dir + "/" + self.__test_case_name + ".robot").unlink()

        # Upload robot result files
        result_files = [glob(self.__result_dir + file) for file in ['/*.xml', '/*.html']]
        for list in result_files:
            for result_file in list:
                self.__tbcs.upload_file_to_execution(self.product_id, self.test_case_id, self.execution_id, result_file)

        # Check if robot framework call failed
        returncode = executed_cmd['subprocess_instance'].returncode

        if returncode != 0:
            if returncode == 252:
                self.__logger.error("Could not find a Robot Testcase with name: '" + executed_cmd['name'] + "'")
            elif returncode > 0 and returncode < 251:
                self.__logger.error(str(returncode) + " failed test case(s).")
            else:
                self.__logger.error("Return Code: " + str(returncode))

            return "Failed"

        else:
            return "Passed"

    # This method is called after all tests are executed.
    def final_cleanup(self):
        self.__logger.info('Final cleanup')
        # Do some adapter specific cleanup
        if config.ROBOT_KDT['cleanup']:
            rmtree(self.__result_dir,
                   ignore_errors=True,
                   onerror=self.__logger.warn("Removing result directory failed!"))

        # remove logger instances (save memory)
        logger_utils.remove_logger(self.__logger.name)
        pass
