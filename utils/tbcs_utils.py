import argparse
import os
from datetime import datetime
from logging import Logger
from typing import List, Union

import config

import utils.comparison_utils as comparison_utils
from utils.tbcs_api import TbcsApi


def connect_itb(logger: Logger, account: dict) -> TbcsApi:
    """
    Log in to TestBench CS using the login data configured.

    Parameters
    ----------
    logger: logging.Logger
        Logger instance        

    account : dict
        Dictionary of all necessary information needed to log into TestBench CS
        - TBCS_BASE
        - WORKSPACE
        - LOGIN
        - PASSWORD

    Returns
    -------
    TbcsApi
    - instance of a new TbcsApi
    """
    logger.info(f"Login to workspace '{account['WORKSPACE']}' at '{account['TBCS_BASE']}' ...")
    try:
        tbcs = TbcsApi.setup(
            account['TBCS_BASE'],
            account['WORKSPACE'],
            account['LOGIN'],
            account['PASSWORD'],
        )
    except Exception as e:
        logger.debug(
            f"Login failed with response:\n\t{e.__str__()}\n\tIn: {e.__traceback__.tb_frame.f_code}\n\tAt Line: {e.__traceback__.tb_lineno}"  # pyright: reportOptionalMemberAccess=false
        )
        logger.error(f"Login failed! Please check your credentials. If you use an insecure server use the '-i' flag.")
        exit(1)
    logger.info(f"Successfully logged in as (id - login): {tbcs.user_id} - {account['LOGIN']}")

    return tbcs


def get_products(logger: Logger, tbcs: TbcsApi, product_filter: dict) -> List[str]:
    """
    Get the id of each product matching the filter and return as list of these product ids.

    Parameters
    ----------
    logger: logging.Logger
        Logger instance
    
    tbcs: TbcsApi
        TbcsApi instance

    product_filter: dict
        Dictionary used to retrieve only specific products

    Returns
    -------
    List[str]
    - product_ids => The result only contains products the user has product role(s) assigned
    """
    logger.info("Scanning Products ...")
    products = tbcs.get_products()
    product_ids = []
    for product in products:
        if comparison_utils.is_matching(product, product_filter):
            product_ids.append(str(product['id']))
            logger.info(f"Found matching Product (id - name): {product['id']} - {product['name']}")

    if len(product_ids) == 0:
        logger.info("No matching Products found.")

    return product_ids


def ask_for_product(logger: Logger, tbcs: TbcsApi) -> str:
    """
    Presents a list of products and asks the user to select one.

    Parameters
    ----------
    logger: logging.Logger
        Logger instance
    
    tbcs: TbcsApi
        TbcsApi instance

    Returns
    -------
    product_id
    - product_id => Id of the selected product
    - "" => If no valid product was selected
    """
    from utils.terminal_utils import input

    product_id = ""
    product_ids = get_products(logger, tbcs,
                               config.PRODUCT_FILTER)  # only products existing during TA-Agent startup are captured

    if not product_ids:
        return product_id

    all_products = tbcs.get_products()

    print("Available products:")

    for product in all_products:
        if str(product['id']) in product_ids:
            print(f"{product['id']}: {product['name']}")

    print("\nSelect product for import: ")
    product_selection = input("Product ID: ")

    if product_selection in product_ids:
        product_id = product_selection
    else:
        logger.info(f"Invalid product ID: {product_selection} - terminating.")
        return ""

    logger.info(f"Using product: {product_id}")

    return product_id


def get_test_suites(logger: Logger, tbcs: TbcsApi, product_id: str, ts_filter: dict) -> List[str]:
    """
    Get id of each Test Suite that matches the criteria configured

    Parameters
    ----------
    logger: logging.Logger
        Logger instance
    
    tbcs: TbcsApi
        TbcsApi instance

    product_id: str
        Id of the product that contains the Test Suite

    ts_filter: dict
        Dictionary used to retrieve only specific Test Suites

    Returns
    -------
    List[str]
    - test_suite_ids => The result only contains Test Suite that match the given filter
    """
    logger.info(f"Scanning Test Suites for product with id: {product_id}")
    test_suites = tbcs.get_suites(product_id)
    test_suite_ids = []
    for test_suite in test_suites:
        if comparison_utils.is_matching(test_suite, ts_filter):
            test_suite_ids.append(str(test_suite['testSuiteId']))
            logger.info(f"Found matching Test Suite (id - name): {test_suite['testSuiteId']} - {test_suite['name']}")

    if len(test_suite_ids) == 0:
        logger.info("No matching Test Suites found.")

    return test_suite_ids


def get_test_sessions(logger: Logger, tbcs: TbcsApi, product_id: str, ts_filter: dict) -> List[str]:
    """
    Get id of each Test Session that matches the criteria configured

    Parameters
    ----------
    logger: logging.Logger
        Logger instance
    
    tbcs: TbcsApi
        TbcsApi instance

    product_id: str
        Id of the product that contains the Test Session

    ts_filter: dict
        Dictionary used to retrieve only specific Test Sessions

    Returns
    -------
    List[str]
    - test_session_ids => The result only contains Test Sessions that match the given filter
    """
    logger.info(f"Scanning Test Sessions for product with id: {product_id}")
    test_sessions = tbcs.get_sessions(product_id)
    test_session_ids = []
    for test_session in test_sessions:
        if comparison_utils.is_matching(test_session, ts_filter):
            test_session_ids.append(str(test_session['testSessionId']))
            logger.info(
                f"Found matching Test Suite (id - name): {test_session['testSessionId']} - {test_session['name']}")

    if len(test_session_ids) == 0:
        logger.info("No matching Test Session found.")

    return test_session_ids


def create_test_session(logger: Logger, tbcs: TbcsApi, product_id: str, session_name: str) -> str:
    """
    Create a new Test Session in TestBench CS to document the test execution(s).

    Parameters
    ----------
    logger: logging.Logger
        Logger instance
    
    tbcs: TbcsApi
        TbcsApi instance

    product_id: str
        Id of the product

    session_name: str
        Name of the new created Test Session

    Returns
    -------
    str 
    - test_session_ids => The result only contains Test Sessions that match the given filter
    """
    prefix = ""
    if config.TEST_SESSION_PREFIX != "":
        prefix = f"{config.TEST_SESSION_PREFIX}-"
    session_id = tbcs.post_session(product_id,
                                   f"{prefix}{session_name}-{datetime.now().replace(microsecond=0).isoformat()}")

    body = {"responsibles": [tbcs.user_id], "addParticipants": [tbcs.user_id], "status": "Planned"}

    tbcs.patch_session(product_id, session_id, body)

    return session_id


def get_custom_field(logger: Logger, tbcs: TbcsApi, test_case_item: dict, custom_field_name: str) -> str:
    """
    Looks up a specific custom field in a test case.

    Parameters
    ----------
    logger: logging.Logger
        Logger instance
    
    tbcs: TbcsApi
        TbcsApi instance

    test_case_item: dict
        Dictionary of a Test Case

    custom_field_name: str
        Name of the Custom Field

    Returns
    -------
    - str => Value of the Custom Field if found
    - None => if Custom Field could not be found or isn't filled in
    """
    logger.info(f"Scanning Custom Fields of Test Case '{test_case_item['name']}' for '{custom_field_name}' ...")
    found = False
    custom_field_list = tbcs.get_custom_field_list()

    custom_field_id = -1
    for custom_field in custom_field_list:
        if custom_field['name'] == custom_field_name:
            custom_field_id = custom_field['id']
            found = True
            break

    if not found:
        logger.warning(f"Custom Field '{custom_field_name}' not found in TBCS")
        return ""

    found = False

    # search in test case for custom field
    custom_fields = test_case_item['customFields']

    value = ""
    for custom_field in custom_fields:
        if custom_field['customFieldId'] == custom_field_id:
            value = custom_field['value']
            found = True
            break

    if not found:
        logger.warning(f"Custom Field '{custom_field_name}' not filled in Test Case '{test_case_item['name']}'")
        return ""

    logger.info(
        f"Found Custom Field '{custom_field_name}' with value '{value}' in Test Case '{test_case_item['name']}'")
    return value


def get_or_create_CF(logger: Logger,
                     tbcs: TbcsApi,
                     fieldList: List[str],
                     groupname: str = "CFGroup",
                     type: str = "TestCase",
                     anchor: str = "BeforeDescription",
                     create: bool = True) -> dict:
    """
    Checks if a keyword exists, otherwise it will be created.

    Parameters
    ----------
    logger: logging.Logger
        Logger instance
    
    tbcs: TbcsApi
        TbcsApi instance

    fieldList: List[str]
        List of custom field names to retrieve                

    groupname: str
        name of section to use or create

    type: str
        (optional) element type to place container in, one of: Epic, UserStory, TestCase (default), Execution, Defect, TestSuite, TestSession

    anchor: str
        (optional) position within element to place container in, availability depends on type. One of: 
        BeforeDescription (default), BeforePreconditions, BeforeTestExecutionHistory, BeforeTestSequence, 
        BeforeTestExecution, BeforeAutomation, BeforeTestCases, Bottom

    create: bool
        (optional) if True (default) try to create missing CF and blocks
        if False, don't create, just return ids for existing CF

    Returns
    -------
    dict
    - dictionary of custom field names with their ids in TestBench
    - Keys are uppercase to support easier matching
    """

    cfRaw = tbcs.get_custom_field_list()
    cfLookup = {}
    for cf in cfRaw:
        cfLookup[cf['name'].upper()] = cf['id']

    cfBlockList = tbcs.get_custom_field_block_list()

    if create == True:
        blockId = 0
        cfInBlock = []
        for block in cfBlockList:
            if block['name'].upper() == groupname.upper():
                blockId = block['id']
                cfInBlock = block['customFieldIds']
                break

        if blockId == 0:
            blockId = tbcs.add_custom_field_block(groupname)

        for field in fieldList:
            if field.upper() not in cfLookup:
                fieldId = 0
                try:
                    fieldId = tbcs.add_custom_field(field[0].upper() + field[1:])
                    cfLookup[field.upper()] = fieldId
                    cfInBlock.append(fieldId)
                except:
                    logger.error(f"Could not create Custom Field: {field}")
                try:
                    if fieldId != 0:
                        tbcs.patch_custom_field_block(blockId, cfIdList=cfInBlock)
                except:
                    logger.error(f"Could not assign custom field {field} to block {groupname}")

        containerList = tbcs.get_custom_field_containers()

        # containerType = "TestCase"
        # anchor = "BeforeDescription"
        containerBlockList = []
        for container in containerList:
            if container['containerType'] == type:
                for block in container['customBlocks']:
                    if block['anchor'] == anchor:
                        containerBlockList = block['blockIds']
        if blockId not in containerBlockList:
            containerBlockList.append(blockId)
            try:
                tbcs.update_custom_field_containers(containerBlockList, container=type, anchor=anchor)
            except:
                logger.error(f"Could not assign custom field group {groupname} at anchor {anchor}")

    return cfLookup


def par_in_List(par: dict, par_list: [dict]) -> bool:
    result = False
    for list_par in par_list:
        if list_par['name'] == par['name']:
            result = True
            break

    return result


def get_or_create_kwd(logger: Logger,
                      tbcs: TbcsApi,
                      product_id: str,
                      new_keyword: dict,
                      signature_check: bool = False,
                      update_level: int = 0) -> dict:
    """
    Checks if a keyword exists, otherwise it will be created.
    'exists' can mean:
     * keyword with the same name exists (ignoring caps)
     * keyword has been renamed but the original name wass the same (ignoring caps, whitespace ...)
     * keyword has inline parameters subsituted (only BDT)

    Parameters
    ----------
    logger: logging.Logger
        Logger instance
    
    tbcs: TbcsApi
        TbcsApi instance

    product_id: str
        Id of the product

    new_keyword: dict
        Dictionary of the new keyword

    signature_check: boolean
        Checks the signature of a keyword.
        By default, set to "False"

    update_level: int
        defines if existing Keywords shall be updated
        0: no updates (default)
        1: update name or description
        2: update parameter list

    Returns
    -------
    dict
    - id => Id of the found keyword
    - par_list => List of the parameters containing dictionaries (keys: id, name, description)
    - {} => if the signature of the keyword is wrong
    """
    if tbcs.keyword_list == {}:
        tbcs.keyword_list = tbcs.get_keyword_list(product_id)
    keyword_list = tbcs.keyword_list

    name = new_keyword['name']
    description = new_keyword['description']
    if description == None:
        description = ""

    variables = {}
    if description != "":
        variables['description'] = description
    variables['originalText'] = name
    variables['name'] = name

    par_list = []

    for keyword in keyword_list:
        # check for identical name, identity of name with original text, or if the keyword name is parameterized
        if keyword['name'].upper() == name.upper() or comparison_utils.is_equal_ignore_separators(
                keyword['originalText'], name) or comparison_utils.is_equal_parameterized(keyword['name'], name):

            if keyword['name'].upper() == name.upper():
                logger.debug("name equal")
            if comparison_utils.is_equal_ignore_separators(keyword['originalText'], name):
                logger.debug("name equal original text")
            if comparison_utils.is_equal_parameterized(keyword['name'], name):
                logger.debug(f"name equal ignoring pars: {keyword['name']} - {name}")

            updated = 0
            if update_level > 0 and (description != keyword['description'] or name != keyword['name']):
                print("Updating name/description")
                updated = 1
                variables = {}
                if description != "":
                    variables['description'] = description
                variables['name'] = name
                tbcs.update_keyword(product_id, keyword['id'], variables)

            # check for identical signature:
            mismatch = 0
            # step1: all parameters of new Keyword in old Keyword?
            for parNew in new_keyword['parlist']:
                if not par_in_List(parNew, keyword['parameters']):
                    if update_level > 1:
                        logger.debug(f'Parameter not found in old: {parNew["name"]} - creating!')
                        variables = {}
                        variables['paramName'] = parNew["name"]
                        if 'description' in parNew.keys():
                            variables['paramDescription'] = parNew['description']
                        par_id = tbcs.create_keyword_param(product_id, keyword['id'], variables)
                        par_list.append({
                            'id': par_id,
                            'name': parNew['name'],
                            'description': variables['paramDescription']
                        })
                        updated = updated + 1
                    else:
                        logger.debug(f'Parameter not found in old: {parNew["name"]}')
                        mismatch = mismatch + 1

            # step2: all parameters of old Keyword still in new Keyword?
            for parOld in keyword['parameters']:
                if not par_in_List(parOld, new_keyword['parlist']):
                    if update_level > 1:
                        logger.debug(f'Parameter not found in new: {parOld["name"]} - deleting!')
                        tbcs.delete_keyword_param(product_id, parOld["id"])
                        keyword['parameters'].remove(parOld)
                        updated = updated + 1
                    else:
                        logger.debug(f'Parameter not found in new: {parOld["name"]}')
                        mismatch = mismatch + 1

            if mismatch == 0 or signature_check == False:
                for parameter in keyword['parameters']:
                    par_list.append(parameter)

                logger.debug(f"Found existing Keyword {keyword['name']} with id: {keyword['id']}")
                if updated > 0:
                    return {'id': keyword['id'], 'par_list': par_list, 'action': 'updated'}
                else:
                    return {'id': keyword['id'], 'par_list': par_list, 'action': 'reused'}
            else:
                return {'action': 'none (signature mismatch)'}

    keyword_id = tbcs.create_keyword(product_id, variables)
    logger.debug(f"Successfully created Keyword with id: {keyword_id}")

    if len(new_keyword['parlist']) > 0:
        for arg in new_keyword['parlist']:
            # logger.debug(f"Adding parameter: {arg['name']}")

            variables = {}
            variables['paramName'] = arg['name']
            if 'description' in arg.keys():
                variables['paramDescription'] = arg['description']
            par_id = tbcs.create_keyword_param(product_id, keyword_id, variables)
            if 'paramDescription' in variables:
                par_list.append({'id': par_id, 'name': arg['name'], 'description': variables['paramDescription']})
            # logger.debug(f"Successfully created Parameter with id: {par_id}")

    return {'id': keyword_id, 'par_list': par_list, 'action': 'created'}


def get_test_step_block(logger: Logger, tbcs: TbcsApi, test_case_item: dict, block_name: str) -> Union[dict, None]:
    """
    Looks up a specific custom field in a test case.

    Parameters
    ----------
    logger: logging.Logger
        Logger instance
    
    tbcs: TbcsApi
        TbcsApi instance

    test_case_item: dict
        Dictionary of a Test Case

    block_name: str
        Name of the Custom Field

    Returns
    -------
    - dict => Content of the Test Step Block if found
    - None => if Test Step Block could not be found or isn't filled in
    """
    logger.debug(f"Scanning Test Step Blocks of Test Case '{test_case_item['name']}' for '{block_name}' ...")

    if not test_case_item['testSequence']:
        logger.info('Test Case contains no Test Sequence')
        return None

    if not test_case_item['testSequence']['testStepBlocks']:
        logger.info('Test Case contains no Test Step Blocks')
        return None

    for block in test_case_item['testSequence']['testStepBlocks']:
        if block['title'] == block_name:
            return block

    logger.info(f"Test Case contains no Test Step Block with name '{block_name}'")
    return None


def handle_default_args(account: dict, parser: argparse.ArgumentParser) -> argparse.Namespace:
    """
    Checks if a keyword exists, otherwise it will be created.

    Parameters
    ----------
    account: dict
        Dictionary that contains TestBench CS account information
        - TBCS_BASE
        - WORKSPACE
        - LOGIN
        - PASSWORD

    parser: ArgumentParser
        Instance of an argument parser

    Returns
    -------
    Namespace
        Parser set containing values of parsed arguments
    """
    from utils.terminal_utils import input

    parameter_set = {}

    parser.add_argument('-w', '--workspace', nargs=1, help='your TestBench CS workspace')
    parser.add_argument('-s', '--server', nargs=1, help='base address for TestBench CS Server')
    parser.add_argument('-u', '--user', nargs=1, help='user name for accessing TestBench CS')
    parser.add_argument('-p', '--password', nargs=1, help='password for accessing TestBench CS')
    parser.add_argument('-i',
                        '--insecure',
                        dest='insecure',
                        action='store_const',
                        const=True,
                        default=False,
                        help='for debugging only: ignore SSL warnings')

    parameter_set = parser.parse_args()

    # for debugging on local setups -->
    import urllib3

    if parameter_set.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # type: ignore
        TbcsApi.verify = False
    # <-- for debugging on local setups

    if parameter_set.workspace != None:
        account['WORKSPACE'] = parameter_set.workspace[0]
    if parameter_set.user != None:
        account['LOGIN'] = parameter_set.user[0]
    if parameter_set.password != None:
        account['PASSWORD'] = parameter_set.password[0]
    if parameter_set.server != None:
        account['TBCS_BASE'] = parameter_set.server[0]

    if account['TBCS_BASE'][-1] in "/\\":
        account['TBCS_BASE'] = account['TBCS_BASE'][0:-1]

    if account['TBCS_BASE'] == "":
        account['TBCS_BASE'] = "https://cloud01-eu.testbench.com"
    if account['WORKSPACE'] == '':
        account['WORKSPACE'] = input("Please enter your TestBench CS workspace name: ")
    if account['LOGIN'] == "":
        account['LOGIN'] = input(f"Please enter your login name for TestBench CS <{account['WORKSPACE']}>: ")
    if account['PASSWORD'] == "":
        account['PASSWORD'] = input("Please enter your password: ")

    return parameter_set


def get_files(logger: Logger, source: List[str], file_extension="") -> List[str]:
    """
    Recursivly scans a list of files and or folders for file contents.

    Parameters
    ----------
    logger: logging.Logger
        Logger instance

    source: List[str]
        A list of files and/or folders to be scanned for files

    file_extension: str
        If set only files with this extension are returned

    Returns
    -------
    List[str]
        A list of all filepaths found for the given source argument
    """
    results: List[str] = []
    for s in source:
        if os.path.isfile(s):
            if file_extension and not s.endswith("." + file_extension):
                continue

            results.append(s)
            logger.debug(f'appending file {s} to file list')
            continue

        if os.path.isdir(s):
            logger.debug(f'scanning folder {s}')
            # recursivly scan folder
            for folder, _, files in os.walk(s):
                for file in files:
                    if file_extension and not file.endswith("." + file_extension):
                        continue

                    fullpath = os.path.join(folder, file)
                    logger.debug(f'appending {fullpath} to file list')
                    results.append(fullpath)
            continue
        logger.error(f'{s} is neither a file nor folder')
        continue
    return results


def get_sections(logger: Logger, tbcs: TbcsApi, product_id: str, tc_id: str) -> dict:
    """
    Retrieves sections (blocks) in a structured Test Case and returns a dictionary with the found sections and their IDs.

    Parameters
    ----------
    logger: logging.Logger
        Logger instance

    tbcs: TbcsApi
        TbcsApi instance

    product_id: str
        Id of the product

    tc_id: str
        Id of the Test Case

    Returns
    -------
    dict:
        A dictionary including the section ids for each section title
    """
    result_sections = {}

    tc = tbcs.get_test_case(product_id, tc_id)

    for section in tc['testSequence']['testStepBlocks']:
        result_sections[section['title']] = section['id']

    return result_sections
