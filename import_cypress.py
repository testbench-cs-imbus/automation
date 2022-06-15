import argparse
import re
from typing import List

import config
import utils.logger_utils as logger_utils
import utils.tbcs_utils as tbcs_utils
from utils.terminal_utils import ProgressIndicator


class Cy_TestStep(object):
    Parent: 'Cy_Test_Case'
    Name: str

    def __init__(self, parent: 'Cy_Test_Case' = None, name: str = '') -> None:  # type: ignore
        self.Parent = parent
        self.Name = name


class Cy_Test_Case(object):
    Parent: 'Cy_User_Story'
    Name: str
    Description: str
    ExternalId: str
    Test_Steps: List[Cy_TestStep]

    def __init__(self, parent: 'Cy_User_Story' = None, name: str = '') -> None:  # type: ignore
        self.Parent = parent
        self.Name = name
        self.Test_Steps = []
        self.Description = ''
        self.ExternalId = ''


class Cy_User_Story(object):
    Parent: 'Cy_Epic'
    Name: str
    Test_Cases: List[Cy_Test_Case]
    FileName: str

    def __init__(self, parent: 'Cy_Epic' = None, name: str = '') -> None:  # type: ignore
        self.Parent = parent
        self.Name = name
        self.Test_Cases = []
        self.FileName = ''


class Cy_Epic(object):
    Name: str
    Stories: List[Cy_User_Story]

    def __init__(self, name: str = '') -> None:
        self.Name = name
        self.Stories = []


# Configure logging
logger = logger_utils.get_logger('CypressImport', config.LOGLEVEL)

# Parse command line
parser = argparse.ArgumentParser(description="Import Test Cases from Cypress specification files.")
parser.add_argument('-d',
                    '--dry-run',
                    dest='dryrun',
                    action='store_const',
                    const=True,
                    default=False,
                    help='only print scanned results')
parser.add_argument('-e', '--epic', nargs='?', default='Cypress', help='epic name to generate')
parser.add_argument("source", nargs="+", default=[''], help='name of one or more files or folders to be scanned')
plist = tbcs_utils.handle_default_args(config.ACCOUNT, parser)

logger.info('\033[0;32mCypress specification import started.\033[0m')
logger.info(f'Using source(s) "{plist.source}"{" with option --dry-run" if plist.dryrun else ""}')
logger.info(f'Using Epic name: "{plist.epic}"')

logger.info('Scanning specifications ...')

files = tbcs_utils.get_files(logger, plist.source)
if len(files) == 0:
    logger.error('No files found for scanning. Skipping ...')
    exit(1)


def __getStoryFromFile(file: str) -> Cy_User_Story:
    story: Cy_User_Story = None  # type: ignore
    try:
        with open(file, 'r') as f:
            for line in f:
                describe_line = re.search('^\s*describe\(\'(.*)\'.*', line)  # type: ignore
                if describe_line:
                    logger.debug(f'describe line found: {line}')
                    story = Cy_User_Story(epic, describe_line.group(1))
                    continue
                it_line = re.search('^\s*it\(\'(.*)\'.*', line)  # type: ignore
                if it_line:
                    logger.debug(f'it line found: {line}')
                    testcase = Cy_Test_Case(story, f'{story.Name} {it_line.group(1)}')
                    story.Test_Cases.append(testcase)
                    continue
                # >>> meta data lines
                descr_line = re.search('^\s*TBCS_DESCRIPTION\(\'(.*)\'.*', line)  # type: ignore
                if descr_line:
                    logger.debug(f'TBCS_DESCRIPTION line found: {line}')
                    testcase.Description = descr_line.group(1)  # type: ignore
                    continue
                extid_line = re.search('^\s*TBCS_AUTID\(\'(.*)\'.*', line)  # type: ignore
                if extid_line:
                    logger.debug(f'TBCS_AUTID line found: {line}')
                    testcase.ExternalId = extid_line.group(1)  # type: ignore
                    continue
                # <<< meta data lines
                log_line = re.search('^\s*cy\.log\(\'(.*)\'.*', line)  # type: ignore
                if log_line:
                    logger.debug(f'log line found: {line}')
                    teststep = Cy_TestStep(testcase, log_line.group(1))  # type: ignore
                    testcase.Test_Steps.append(teststep)  # type: ignore
                    continue
    except Exception as e:
        logger.error(f'Failed to extract Test Cases from file "{file}"\n\t{e.__str__()}')

    return story


progress_bar_files = ProgressIndicator(len(files), 'Scanning', 'Files')
epic = Cy_Epic(plist.epic)
for file in files:
    progress_bar_files.update_progress(file)

    us = __getStoryFromFile(file)
    if us != None:
        us.FileName = file
        epic.Stories.append(us)
ProgressIndicator.clear_indicators()
logger.info('Scanning specifications finished')

tc_found_count = 0
for us in epic.Stories:
    for tc in us.Test_Cases:
        tc_found_count += 1
if tc_found_count == 0:
    logger.warning('No test cases found. Skipping ...')
    exit(1)

logger.info(f'Found {tc_found_count} Test Cases')

if plist.dryrun:
    print('Scan result:\n\n')
    print(f'Epic: {epic.Name}')
    for us in epic.Stories:
        print(f'  User Story: {us.Name} (from file: {us.FileName})')
        for tc in us.Test_Cases:
            print(f'    Test Case: {tc.Name}')
            print(f'     Description: {tc.Description}')
            print(f'     ExternalID: {tc.ExternalId}')
            for ts in tc.Test_Steps:
                print(f'      Test Step: {ts.Name}')
    exit(0)

logger.info(f'Starting import to "{config.ACCOUNT["TBCS_BASE"]}" ...')
tbcs = tbcs_utils.connect_itb(logger, config.ACCOUNT)
pid = tbcs_utils.ask_for_product(logger, tbcs)
if (pid == ""):
    exit(1)

try:
    epicJson = {"name": epic.Name}
    eid = tbcs.post_epic(pid, epicJson)

    cfId = -1
    cfList = tbcs.get_custom_field_list()
    if cfList:
        for cf in cfList:
            if cf["name"] == config.ADAPTER_CUSTOM_FIELD_NAME:
                cfId = cf["id"]

    progress_bar_us = ProgressIndicator(len(epic.Stories), 'Importing', 'User Stories', 60)
    progress_bar_tc = ProgressIndicator(0, 'Importing', 'Test Cases', 60)
    for us in epic.Stories:
        progress_bar_us.update_progress(us.Name)
        logger.debug(f'Importing User Story: \'{us.Name}\' ...')
        usJson = {"epicId": eid, "name": us.Name}
        try:
            uid = tbcs.post_user_story(pid, usJson)
            progress_bar_tc.reset_total(len(us.Test_Cases))

            for tc in us.Test_Cases:
                progress_bar_tc.update_progress(f'{tc.ExternalId} - {tc.Name}')
                try:
                    tcfound = tbcs.get_test_case_by_filter(pid, 'externalId', 'equals', tc.ExternalId)
                    if tcfound != []:
                        logger.debug(f'Test Case with externalID "{tc.ExternalId}" already exists. Updating ...')
                        tcid = str(tcfound[0]['id'])
                        tcPatchJson = {
                            "name": tc.Name,
                            "description": {
                                "text": tc.Description
                            },
                            "isAutomated": True,
                            "toBeReviewed": True,
                            "externalId": {
                                "value": tc.ExternalId
                            },
                        }
                        tbcs.patch_test_case(pid, tcid, tcPatchJson)
                        if cfId >= 0:
                            tcPatchJson = {"customFields": [{"customFieldId": cfId, "value": "Cypress"}]}
                            tbcs.patch_test_case(pid, tcid, tcPatchJson)
                        tcitemfound = tbcs.get_test_case(pid, tcid)
                        block = tbcs_utils.get_test_step_block(logger, tbcs, tcitemfound, "Test Steps")
                        if block != None:
                            blockid = block['id']
                            for step in block['steps']:
                                tbcs.remove_test_step(pid, tcid, step['id'])
                            for ts in tc.Test_Steps:
                                tbcs.add_test_step(pid, tcid, ts.Name, blockid, "TestStep")
                        continue
                    logger.debug(f'Importing Test Case "{tc.Name}" with externalID "{tc.ExternalId}" ...')
                    tcJson = {"userStoryId": uid, "name": tc.Name, "testCaseType": "StructuredTestCase", "customTestSequenceTitles": []}
                    tcid = tbcs.post_test_case(pid, tcJson)

                    tcPatchJson = {
                        "description": {
                            "text": tc.Description
                        },
                        "isAutomated": True,
                        "toBeReviewed": True,
                        "externalId": {
                            "value": tc.ExternalId
                        },
                    }
                    tbcs.patch_test_case(pid, tcid, tcPatchJson)
                    if cfId >= 0:
                        tcPatchJson = {"customFields": [{"customFieldId": cfId, "value": "Cypress"}]}
                        tbcs.patch_test_case(pid, tcid, tcPatchJson)
                    tsbid = tbcs.add_test_step_block(pid, tcid, "Test Steps")
                    for ts in tc.Test_Steps:
                        tbcs.add_test_step(pid, tcid, ts.Name, tsbid, "TestStep")
                except Exception as e:
                    logger.error(
                        f'Failed to import Test Case "{tc.Name}" with externalID "{tc.ExternalId}"\n\t{e.__str__()}')
        except Exception as e:
            logger.error(f'Failed to import User Story "{us.Name}"\n\t{e.__str__()}')
except Exception as e:
    logger.error(f'Unexpected error occured:\n\t{e.__str__()}')
    exit(1)
ProgressIndicator.clear_indicators()
logger.info('Done')
exit(0)
