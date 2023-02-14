#
# Adapter for Robot Framework
#

import json
import subprocess
from pathlib import Path
from shutil import rmtree

import config
import utils.logger_utils as logger_utils

from adapters.AdapterTemplate import AdapterTemplate


class RobotFramework(AdapterTemplate):
    product_id: str
    test_case_id: str
    execution_id: str

    def __init__(self, tbcs, concrete_test_case, abstract_test_case, execution_id, temp_dir):
        self.product_id = str(concrete_test_case['productId'])
        self.test_case_id = str(concrete_test_case['id'])
        self.execution_id = execution_id

        self.__tbcs = tbcs
        self.__concrete_test_case = concrete_test_case
        self.__test_case_name = str(concrete_test_case['name'])
        self.__external_id = 0
        # TODO: AUTOMATION FEHLT! self.__external_id = concrete_test_case['automation']['externalId']

        # Avoid Winerror 206
        self.__concrete_test_case['executions'] = ""

        # Create logger
        self.__logger = logger_utils.get_logger(self.__class__.__name__ + "_" + self.execution_id, config.LOGLEVEL)

        # Save folder paths
        self.__result_dir = str(
            Path(config.ROBOT_KDT['base_dir'] + config.ROBOT_KDT['result_dir'] + "/" + self.__test_case_name)).replace(
                "\\", "/")

        # Create folder for created files, if it doesn't exist
        Path(self.__result_dir).mkdir(parents=True, exist_ok=True)

        self.__logger.info("Adapter initialized")

    def execute_test_case(self, parallel, ddt_row):

        call = [
            "robot",
            "--outputdir",
            self.__result_dir,
        ]

        if self.__external_id:
            # Use external_id for Test Case selection
            call.extend(["-i", "ID:" + str(self.__external_id)])
        else:
            # Use Test Case name for selection
            call.extend(["-t", self.__test_case_name])

        call.extend([
            "--listener", "./addons/robotListener.py;" + str(self.__tbcs.tbcs_base) + ";" + str(self.__tbcs.tenant_id) +
            ";" + str(self.__tbcs.user_id) + ";" + str(self.__tbcs.session_token) + ";" + str(self.__tbcs.verify) +
            ";" + str(json.dumps(self.__concrete_test_case)) + ";" + self.execution_id
        ])

        if ddt_row:
            ddt_name = ""

            for ddt_item in ddt_row:
                call.extend(["--variable", ddt_item['column'] + ":" + ddt_item['value']])
                ddt_name += "_" + ddt_item['column'] + "=" + ddt_item['value']

            self.__test_case_name += ddt_name

        call.extend([
            "--log", self.__test_case_name + "-log.html", "--report", self.__test_case_name + "-report.html",
            "--output", self.__test_case_name + "-output.xml", config.ROBOT_FRAMEWORK["search_dir"]
        ])

        try:
            if parallel:
                # Call to execute robot framework test cases parallel
                return subprocess.Popen(call)
            else:
                # Call to execute robot framework test cases sequential
                return subprocess.run(call)
        except Exception as e:
            self.__logger.error(f"Subprocess method failed!\n\t{e.__str__()}")
            return None

    def check_result(self, executed_cmd):
        # Check if robot framework call failed
        returncode = executed_cmd['subprocess_instance'].returncode

        if returncode != 0:
            if returncode == 252:
                self.__logger.error("Could not find a Robot Testcase with name: '" + executed_cmd['name'] + "'")
            elif returncode > 0 and returncode < 251:
                self.__logger.error(str(returncode) + " failed test case(s).")
            else:
                self.__logger.error("Return Code is: " + str(returncode))

            return "Failed"

        else:
            return "Passed"

    # This method is called after all tests are executed.
    def final_cleanup(self):
        self.__logger.info('Final cleanup')
        # Do some adapter specific cleanup
        if config.ROBOT_FRAMEWORK['cleanup']:
            rmtree(self.__result_dir,
                   ignore_errors=True,
                   onerror=self.__logger.warn("Removing result directory failed!"))

        # remove logger instances (save memory)
        logger_utils.remove_logger(self.__logger.name)

        pass
