#
# Adapter Template
#

import subprocess
from tempfile import TemporaryDirectory
from typing import List, Union

import config
import utils.logger_utils as logger_utils
from utils.tbcs_api import TbcsApi


class AdapterTemplate:

    # public variables needed by agent
    product_id: str
    test_case_id: str
    execution_id: str

    # Default constructor for adapter initialization
    def __init__(self, tbcs: TbcsApi, concrete_test_case: dict, abstract_test_case: dict, execution_id: str,
                 temp_dir: TemporaryDirectory):
        """
        Initializes the Adapter.

        Parameters
        ----------
        tbcs: TbcsApi
            Instance of the TbcsApi for communication with TestBench CS

        concrete_test_case: dict
            Dictionary containing all concrete information of a Test Case

        abstract_test_case: dict
            Dictionary containing all abstract information of a Test Case

        execution_id: str
            Id of the Execution

        temp_dir: TemporaryDirectory
            Temporary directory containing attachments of a Test Case

        Returns
        -------
        AdapterTemplate
            A new instance of an Adapter
        """
        self.product_id: str = str(concrete_test_case['productId'])
        self.test_case_id: str = str(concrete_test_case['id'])
        self.execution_id: str = execution_id

        self.__test_case_name: str = str(concrete_test_case['name'])
        # following private variables can be used as needed
        self.__tbcs: TbcsApi = tbcs
        self.__concrete_test_case: dict = concrete_test_case
        self.__abstract_test_case: dict = abstract_test_case
        self.__external_id: str = concrete_test_case['automation']['externalId']
        self.__temp_dir: TemporaryDirectory = temp_dir

        # Create logger
        self.__logger = logger_utils.get_logger(self.__class__.__name__ + "_" + self.execution_id, config.LOGLEVEL)

        # Here can come some additional initalization code
        # ...
        #
        self.__logger.info("Adapter initialized")

    def execute_test_case(self, parallel: bool,
                          ddt_row: List[dict]) -> Union[subprocess.Popen, subprocess.CompletedProcess, None]:
        """
        This function executes the given Test Case
        
        Parameters
        ----------
        parallel: bool
            Value defines if Test Case should run non blocking

        ddt_row: List[dict]
            List of column - value pairs of a DDT row ([{column: "FirstColumn", value: "1"}, {column: "SecondColumn", value: "2"}, ...])

        Returns
        -------
        - Popen if Test Case runs non blocking
        - CompletedProcess if Test Case runs blocking
        - None if the call failes
        """
        call: List[str] = [
            # Bash call you want to execute
        ]

        if ddt_row:
            # If the Test Case is data-driven, you can read the values from the parameter 'ddt_row'
            cmd, parameters = ''
            for column in ddt_row:
                if column['column'] == 'cmd':
                    cmd = column['value']
                if column['column'] == 'parameters':
                    parameters = column['value']

            # Extend your call with the arguments you get from the DDT-Table
            call.extend([cmd, parameters])

        self.__logger.info(f"Starting Test Case: {self.__test_case_name} ...")

        try:
            if parallel:
                # Call to execute test cases parallel
                return subprocess.Popen(call, shell=True)
            else:
                # Call to execute test cases sequential
                return subprocess.run(call, shell=True)
        except subprocess.SubprocessError as e:
            self.__logger.error(
                f"Subprocess Exception occured for Test Case '{str(self.__test_case_name)}'!\n\t{e.__str__()}")
            return None

    def check_result(self, executed_cmd: dict) -> str:
        """
        This method checks the result of the executed command.

        Parameters
        ----------
        executed_cmd: dict
            Dictionary containing the following key-value pairs:
            - name: str
            - adapter_instance: str
            - subprocess_instance: CompletedProcess || Popen
            - parallel: bool
            - ddt_row: List[dict]

        Returns
        -------
        str
            Result of the Execution as a String ("Passed" or "Failed")
        """
        # Check if call failed
        returncode: int = executed_cmd['subprocess_instance'].returncode

        if returncode == 0:
            return "Passed"

        return "Failed"

    def final_cleanup(self) -> None:
        """
        This method is called after tests have been executed and does some adapter specific cleanup.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        self.__logger.info('Final cleanup')
        # Do some adapter specific cleanup

        # remove logger instances (save memory)
        logger_utils.remove_logger(self.__logger.name)
        pass
