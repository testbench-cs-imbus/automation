#
# Adapter for Cypress
# https://www.cypress.io/
#

import codecs
import glob
import os
import re
import subprocess
from pathlib import Path

import config
import utils.logger_utils as logger_utils


class Cypress:
    # public variables needed by agent
    product_id: str
    test_case_id: str
    execution_id: str

    def __init__(self, tbcs, concrete_test_case, abstract_test_case, execution_id, temp_dir):
        self.product_id = str(concrete_test_case['productId'])
        self.test_case_id = str(concrete_test_case['id'])
        self.execution_id = execution_id

        self.__test_case_name = str(concrete_test_case['name'])
        self.__tbcs = tbcs
        self.__external_id = concrete_test_case['automation']['externalId']
        self.__execution_id = execution_id
        self.__tmpFileEnding = ".tbcs-agent-temp.js"

        # Create logger
        self.__logger = logger_utils.get_logger(self.__class__.__name__ + "_" + self.__execution_id, config.LOGLEVEL)

        # create file for test session ID
        self.__test_session_id_file = Path(config.CYPRESS['base_dir'] + "/testSessionId.txt")
        file = codecs.open(str(self.__test_session_id_file), "w", "utf-8")
        file.write(self.__tbcs.test_session_id)
        file.close()

        self.__logger.info("Adapter initialized")

    def execute_test_case(self, parallel, _):
        if not str(self.__external_id):
            self.__logger.error(
                f"Field 'External ID' in TestBench Test Case '{self.__test_case_name}' not set! Cant search Cypress Specs without an 'External ID' Skipping ..."
            )
            return None

        cypress_root_folder = config.CYPRESS["base_dir"]
        cypress_bin = config.CYPRESS["cypress_bin"]
        cypress_spec_folder = config.CYPRESS["cypress_spec_folder"]

        # find the test case by external ID within the specs
        self.__logger.info(f"Scanning Cypres Specs for Test Case with 'External ID' '{self.__external_id}' ...")
        file_found = ""
        file_fullPath = ""
        rootdir = os.path.join(cypress_root_folder, cypress_spec_folder)
        for folder, _, files in os.walk(rootdir):
            if file_found != "": break
            for file in files:
                if file.endswith(self.__tmpFileEnding): continue
                if file_found != "": break
                fullpath = os.path.join(folder, file)
                with open(fullpath, 'r') as f:
                    for line in f:
                        if str(self.__external_id) in line:
                            file_fullPath = fullpath
                            file_found = cypress_spec_folder + '/**/' + file  # file name sytax especially for Cypress
                            self.__logger.info(
                                f"Test Case with 'External ID' '{self.__external_id}' found in Spec '{file_fullPath}'")
                            break

        if (file_found == ""):
            self.__logger.error(f"Test Case with 'External ID' '{self.__external_id}' not found! Skipping ...")
            return None

        if self.__getTemporarySpec(file_fullPath, self.__tmpFileEnding) == None:
            self.__logger.error("Failed to generate a temporary Spec file for single (it.only) execution! Skipping ...")
            return None

        call = [
            cypress_bin, "run", "--env",
            "extid=" + self.__execution_id + ",tenantid=" + self.__tbcs.tenant_id + ",productid=" + self.product_id +
            ",tbcsurl=" + config.ACCOUNT["TBCS_BASE"] + ",sessiontoken=" + self.__tbcs.session_token, "--spec",
            file_found + self.__tmpFileEnding
        ]

        self.__logger.info(f"Starting Test Case: {str(self.__test_case_name)} ...")

        # Wait for processes to finish if parallel == false
        try:
            if parallel:
                # Call to execute test cases parallel
                return subprocess.Popen(call, cwd=cypress_root_folder)
            else:
                # Call to execute test cases sequential
                return subprocess.run(call, cwd=cypress_root_folder)
        except Exception as e:
            self.__logger.error(
                f"Subprocess Exception occured for Test Case '{str(self.__test_case_name)}'!\n\t{e.__str__()}")
            return None

    def check_result(self, executed_cmd):
        # Check if call failed
        returncode = executed_cmd['subprocess_instance'].returncode

        if returncode == 0:
            return "Passed"

        return "Failed"

    # This method is called after all tests are executed.
    def final_cleanup(self):
        self.__logger.debug('Final cleanup')
        # Do some adapter specific cleanup
        fileList = glob.glob(os.path.join(config.CYPRESS["base_dir"], config.CYPRESS["cypress_spec_folder"]) + '/**/*' +
                             self.__tmpFileEnding,
                             recursive=True)
        # Iterate over the list of filepaths & remove each file.
        for filePath in fileList:
            try:
                os.remove(filePath)
            except OSError:
                self.__logger.error(f'Error while deleting file: {filePath}')

        # remove file with test session id
        try:
            os.remove(self.__test_session_id_file)
        except OSError as e:
            self.__logger.debug(f'Deleting file {self.__test_session_id_file} failed.\n\t{e}')

        # remove logger instances (save memory)
        logger_utils.remove_logger(self.__logger.name)

    def __getTemporarySpec(self, specFileName, tmpFileEnding):
        itPattern = "it\('.+',"  # pyright: reportInvalidStringEscapeSequence=false
        lastItIndex = 0
        fileContents = []
        found = False

        with open(specFileName) as org:
            fileContents = org.readlines()

        for i, line in enumerate(fileContents):
            matchIt = re.search(itPattern, line)
            if (matchIt):
                lastItIndex = i

            matchId = re.search(self.__external_id, line)
            if (matchId):
                fileContents[lastItIndex] = re.sub(r'it\(', 'it.only(', fileContents[lastItIndex])
                found = True
                break

        if (found):
            tmpFileName = specFileName + tmpFileEnding
            with open(tmpFileName, 'w') as f:
                for item in fileContents:
                    f.write(item)
            return tmpFileName
        return None
