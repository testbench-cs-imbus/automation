# Global imports
import argparse
import importlib
import json
from ssl import SSLError
import traceback
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep

# Import adapters, config and utils
import adapters
import config
import utils.comparison_utils as comparison_utils
import utils.logger_utils as logger_utils
import utils.tbcs_utils as tbcs_utils


def get_test_case_attachment(test_case_item):
    # Get Attachments from Test Case if they exist
    if test_case_item['attachments'] == []:
        return None

    logger.info(f"Downloading Attachments of Test Case '{test_case_item['name']}' ...")
    temp_dir = TemporaryDirectory()

    for item in test_case_item['attachments']:
        file_id = str(item['fileId'])
        file_response = tbcs.get_file_response(product_id, file_id)

        path = Path(temp_dir.name) / item['name']

        with path.open('xb') as file:  # x: exclusive, b: binary
            file.write(file_response.content)

        logger.info(f"Downloaded Attachment '{item['name']}' to '{str(path)}")
    logger.info(f"Downloading Attachments of Test Case '{test_case_item['name']}' finished")

    return temp_dir


def get_adapter_instance(tbcs, concrete_test_case, abstract_test_case, execution_id, temp_dir):
    # Find out which Test Tool is defined by the user
    # and return the associated adapter

    # Searches for custom field "Test Tool" and retrieves it
    adapter_name = tbcs_utils.get_custom_field(logger, tbcs, concrete_test_case, config.ADAPTER_CUSTOM_FIELD_NAME)

    # Choose config adapter if not set in TestBench CS
    if adapter_name == '':
        logger.info(f"Custom Field for Adapter not set. Trying default from configuration: '{config.ADAPTER_DEFAULT}'")
        adapter_name = config.ADAPTER_DEFAULT

    if adapter_name in adapters.__all__:
        module = importlib.import_module("adapters." + adapter_name)
        _class = getattr(module, adapter_name)
        logger.info(f"Adapter found. Using: \033[1;32m{str(_class.__name__)}\033[0m")
        return _class(tbcs, concrete_test_case, abstract_test_case, execution_id, temp_dir)

    logger.error(f"Adapter '{adapter_name}' not found! Skipping Test Case '{concrete_test_case['name']}' ...")
    return None


def execute_test_case(tbcs, product_id, test_case_execution):
    # Prepare execution of a single Test Case (a DDT-Test Case-Row or other Test Case type)
    # and then delegate the execution to pycsTestRunner

    test_case_item = tbcs.get_test_case(product_id, str(test_case_execution['testCaseIds']['testCaseId']))

    # For DDT both (abstract and concrete) Test Case will be hand over to the adapter
    abstract_test_case = test_case_item

    test_case_id = str(test_case_item['id'])

    # Create a temporary directory, if test case has attachment(s)
    temp_dir = get_test_case_attachment(test_case_item)

    ddt_table_ids = test_case_execution['testCaseIds'].get("ddtTableIds", [])

    # Check if Test Case has DDT Table
    ddt_row = None
    if ddt_table_ids != None and ddt_table_ids != []:
        # Test Case is a DDT Test Case row = a list of colName, colValue pairs:
        # [{'column':<colName>, 'value':<colValue>}, ... ]
        test_case_ddt_table_id, test_case_ddt_row_id = (
            ddt_table_ids['tableId'],
            ddt_table_ids['rowId'],
        )

        ddt_row = tbcs.get_ddt_row(product_id, test_case_id, test_case_ddt_table_id, test_case_ddt_row_id)

        # Get concrete Test Case
        concrete_test_case = json.dumps(
            tbcs.get_concrete_test_case(product_id, test_case_id, test_case_ddt_table_id,
                                        test_case_ddt_row_id)).replace("#*#", "")

        concrete_test_case = json.loads(concrete_test_case)

    else:
        concrete_test_case = test_case_item
        # No DDT Test Case

    # Get adapter from Custom Field or config file
    #global adapter_instance
    adapter_instance = get_adapter_instance(tbcs, concrete_test_case, abstract_test_case,
                                            str(test_case_execution['executionId']), temp_dir)

    if not adapter_instance:
        return

    # Check if Test Case should run parallel
    parallel = comparison_utils.stringToBoolean(
        tbcs_utils.get_custom_field(logger, tbcs, concrete_test_case, "Parallel"))
    if parallel == '':
        # custom field 'Parallel' not defined in TestBench CS => config file
        logger.info(f"Custom Field for 'Parallel' not set. Trying default from configuration: '{config.PARALLEL}'")
        parallel = config.PARALLEL

    # Execute Test Case with given Adapter
    logger.info(
        f"Starting execution of Test Case '{concrete_test_case['name']}' with Adapter '{adapter_instance.__class__.__name__}' ..."
    )
    subprocess_instance = adapter_instance.execute_test_case(parallel, ddt_row)

    if not subprocess_instance:
        logger.error(
            f"Something went wrong while starting the execution with Adapter '{adapter_instance.__class__.__name__}' for Test Case '{concrete_test_case['name']}'. Check previous logs"
        )
        # Ff subprocess failed the execution result in CS stays pending
        return

    running_cmd = {
        'name': concrete_test_case['name'],
        'adapter': adapter_instance,
        'subprocess_instance': subprocess_instance,
        'parallel': parallel,
        'ddt_row': ddt_row
    }

    return running_cmd  # return command which has been started


def collect_test_results(tbcs, running_cmds):
    # Collect results from finished running_cmds
    # and upload them back into iTB
    while running_cmds:
        cmd = running_cmds[0]

        # Check if command is still running and subprocess didn't fail
        if cmd['parallel'] and cmd['subprocess_instance']:
            if cmd['subprocess_instance'].poll() == None:
                running_cmds.pop(0)
                running_cmds.append(cmd)
                continue

        # Remove finished command from list
        running_cmds.pop(0)

        if cmd['subprocess_instance']:
            result = cmd['adapter'].check_result(cmd)
        else:
            result = "Failed"  # Subprocess failed

        tbcs.patch_execution(
            cmd['adapter'].product_id,
            cmd['adapter'].test_case_id,
            cmd['adapter'].execution_id,
            {'executionResult': result},
        )

        # If screenshot flag is set, the agent uploads a screenshot into the Test Case description
        if plist.screenshot:
            file_id = tbcs.upload_file_to_execution(
                cmd['adapter'].product_id,
                cmd['adapter'].test_case_id,
                cmd['adapter'].execution_id,
                plist.screenshot[0],
            )['fileId']

            description = tbcs.get_test_case(cmd['adapter'].product_id, cmd['adapter'].test_case_id)['description']

            # Check if Test Case already contains an image
            if "![ File not found or not an image!]" in description:
                start = description.find("fileIds=") + 8
                end = description.find(' ', start)
                description = description[:start] + str(file_id) + description[end:]
            else:
                description += f"\n\n![ File not found or not an image!]({config.ACCOUNT['TBCS_BASE']}/api/tenants/{tbcs.tenant_id}/products/{product_id}/file/download?element=TestCase&fileIds={file_id} 'screenshot.png')"

            tbcs.patch_test_case(
                cmd['adapter'].product_id,
                cmd['adapter'].test_case_id,
                {"description": {
                    "text": description
                }},
            )

        result_string = "\033[1;32mPASSED\033[0m" if result == "Passed" else "\033[1;31mFAILED\033[0m"
        logger.info(f"{result_string} Test Case '{cmd['name']}'")

        # final cleanup after each test
        cmd['adapter'].final_cleanup()


def execute_test_session(tbcs, product_id, test_session_id):
    # execute all Test Cases in test_case_list and update Test Session status

    logger.info(f"Starting Test Session with id: {test_session_id}")
    test_session = tbcs.get_session(
        product_id,
        test_session_id)
    tbcs.patch_session(product_id, test_session_id, {'status': 'InProgress'})
    tbcs.join_session(product_id, str(test_session_id))

    startTimeUTC = datetime.utcnow()
    startTime = datetime.utcnow().isoformat().split('.')
    startTime = startTime[0] + '.' + startTime[1][:3] + 'Z'
    logger.debug("Start time of Test Session: " + startTime)

    test_case_executions = test_session['testCaseExecutions']

    running_cmds = []
    for test_case_execution in test_case_executions:
        running_cmd = execute_test_case(tbcs, product_id, test_case_execution)

        if running_cmd != None:
            running_cmds.append(running_cmd)

    # Collect results of executed tests
    collect_test_results(tbcs, running_cmds)

    # Set start and end time of Test Session and set status to Completed
    stopTime = datetime.utcnow().isoformat().split(".")
    stopTime = stopTime[0] + "." + stopTime[1][:3] + "Z"
    logger.debug("Stop time of Test Session: " + str(stopTime))
    tbcs.patch_session(product_id, test_session_id, {'startTime': startTime, 'stopTime': stopTime})
    tbcs.patch_session(product_id, test_session_id, {'status': 'Completed'})

    logger.info(
        f"Finished Test Session with id: {test_session_id}. Elapsed time: {str(datetime.utcnow() - startTimeUTC)}")


# --------------------------------
if __name__ == "__main__":
    # Configure logging
    logger = logger_utils.get_logger('Agent', config.LOGLEVEL)

    try:
        # Parse command line
        parser = argparse.ArgumentParser(
            description="Observe TestBench CS Test Suites and start automated test execution if required.")
        parser.add_argument('-l',
                            '--loop',
                            dest='loop',
                            action='store_const',
                            const=True,
                            default=False,
                            help='monitor TestBench CS continously (never stop)')
        parser.add_argument('-sc',
                            '--screenshot',
                            nargs=1,
                            help='uploads a photo from given path into a Test Case description')
        plist = tbcs_utils.handle_default_args(config.ACCOUNT, parser)

        logger.info("\033[0;32mimbus TestBench CS Test Automation Agent - started" +
                    (" in loop mode\033[0m" if plist.loop else " in none loop mode\033[0m"))

        # connect to iTB and select product to monitor
        tbcs = tbcs_utils.connect_itb(logger, config.ACCOUNT)

        # only products existing during TA-Agent startup are captured
        product_ids = tbcs_utils.get_products(logger, tbcs, config.PRODUCT_FILTER)

        # Main loop: poll workspace for Test Sessions ready to run and then execute their Test Cases
        while True:
            try:
                # Process each product which is configured to be monitored
                for product_id in product_ids:
                    # Process each Test Suite in product which is configured to be monitored
                    test_suite_ids = tbcs_utils.get_test_suites(logger, tbcs, product_id, config.TEST_SUITE_FILTER)

                    # From each Test Suite: get the Test Cases and their ids
                    for test_suite_id in test_suite_ids:
                        test_suite = tbcs.get_suite(product_id, test_suite_id)

                        # Check if user is responsible for the Test Suite
                        if not int(tbcs.user_id) in test_suite['responsibles']:
                            logger.warning(
                                f"User '{config.ACCOUNT['LOGIN']}' is not a 'Responsible User' for the Test Suite '{test_suite['name']}'. Skipping ..."
                            )
                            continue

                        # Create Session
                        logger.info(f"Creating Test Session for Test Suite '{test_suite['name']}' ...")
                        test_session_id = tbcs_utils.create_test_session(logger, tbcs, product_id, test_suite['name'])

                        test_case_ids = []
                        for test_case in test_suite['testCases']:
                            if comparison_utils.is_matching(test_case, config.TEST_CASE_FILTER):
                                test_case_ids.append(test_case['testCaseIds'])

                        # Create an execution for every Test Case and append it to the Test Session
                        for test_case_id in test_case_ids:
                            if test_case_id['ddtTableIds']:
                                table_id = test_case_id['ddtTableIds']['tableId']
                                row_id = test_case_id['ddtTableIds']['rowId']
                                execution_id = tbcs.post_execution_ddt(product_id, test_case_id['testCaseId'], table_id,
                                                                       row_id)
                            else:
                                execution_id = tbcs.post_execution(product_id, test_case_id['testCaseId'])

                            tbcs.add_execution_to_session(product_id, test_session_id, test_case_id['testCaseId'],
                                                          execution_id)

                        tbcs.patch_session(product_id, test_session_id, {'status': 'Ready'})
                        logger.info(f"Created Test Session with id: {test_session_id}")

                        # Execute session
                        execute_test_session(tbcs, product_id, test_session_id)

                        tbcs.patch_suite(product_id, str(test_suite['testSuiteId']), {'status': 'Completed'})

                    # Process each Test Session in product which is configured to be monitored
                    test_session_ids = tbcs_utils.get_test_sessions(logger, tbcs, product_id,
                                                                    config.TEST_SESSION_FILTER)

                    for test_session_id in test_session_ids:
                        test_session = tbcs.get_session(product_id, test_session_id)
                        logger.debug("Check Test Session: " + str(test_session['testSessionId']) + " " +
                                     test_session['name'])

                        # Check if user is responsible for the Test Session
                        is_participant = False
                        for participant in test_session['participants']:
                            if str(participant['userId']) == tbcs.user_id:
                                is_participant = True
                                break

                        if not is_participant:
                            logger.warning(
                                f"User '{config.ACCOUNT['LOGIN']}' is not a 'Participating User' in the Test Session '{test_session['name']}'. Skipping ..."
                            )
                            continue

                        # Execute session
                        execute_test_session(tbcs, product_id, test_session_id)

                sleep(config.AGENT_LOOP_INTERVAL_SEC)

                if plist.loop == False:
                    exit(0)

            except SSLError as ce:
                logger.error(f"SSL connection exception occured:\n\t{ce.__str__()}")
                traceback.print_exc()
                print("==============")

    except Exception as e:
        logger.error(f"Exception occured:\n\t{e.__str__()}")
        traceback.print_exc()
        exit(1)
