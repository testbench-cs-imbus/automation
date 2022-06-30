import json
import os
import subprocess
import argparse

import config
import utils.logger_utils as logger_utils
import utils.tbcs_utils as tbcs_utils
from utils.terminal_utils import ProgressIndicator

# Parse command line
parser = argparse.ArgumentParser(description="Import test cases from BDT/Behave.")
parser.add_argument('source', nargs=1, help='name of file or folder to be scanned')
parser.add_argument('-t', '--type', choices=['text', 'keyword'], help='type of test steps to be created')
plist = tbcs_utils.handle_default_args(config.ACCOUNT, parser)

# Configure logging
logger = logger_utils.get_logger('import BDT', config.LOGLEVEL)

if plist.type == "keyword":
    use_KDT = True
else:
    use_KDT = False

filename = plist.source[0].replace("\\", "/")
outFile = config.BEHAVE['base_dir'] + config.BEHAVE['scenario_dir'].replace("\\", "/") + "/out.txt"

call = ["behave", "-d", "-f"
        "json.pretty", "-o", outFile]
call.append(filename)
try:
    res = subprocess.run(call)
except:
    logger.error("Calling 'Behave' failed - is it set up correctly? Terminating ...")
    exit()

if res.returncode != 0:
    logger.error("Behave did not run successfully, please check source parameters.")
    exit(-1)

# connect to iTB and select product to write in
tbcs = tbcs_utils.connect_itb(logger, config.ACCOUNT)

pid = tbcs_utils.ask_for_product(logger, tbcs)
if (pid == ""):
    exit()

# check for CF "Test Tool"
cfId = -1
try:
    fieldList = tbcs_utils.get_or_create_CF(logger, tbcs, [config.ADAPTER_CUSTOM_FIELD_NAME], "Automation")
    if config.ADAPTER_CUSTOM_FIELD_NAME.upper() in fieldList:
        cfId = fieldList[config.ADAPTER_CUSTOM_FIELD_NAME.upper()]
except:
    logger.error(f"Could not create Custom Field: {config.ADAPTER_CUSTOM_FIELD_NAME}")

with open(outFile, 'r') as file:
    obj = json.load(file)

count_created = 0

for feature in obj:
    usName = feature["name"]
    if "description" in feature:
        usDescription = feature["description"]
    else:
        usDescription = ["(no description in feature)"]

    usJson = {"name": usName}
    logger.info("Adding User Story (Feature): " + usName)
    usId = tbcs.post_user_story(pid, usJson)
    usDescText = ""
    for txt in usDescription:
        if usDescText != "":
            usDescText = usDescText + "\n"
        usDescText = usDescText + txt

    usJson['description'] = usDescText

    tbcs.patch_user_story(pid, usId, usJson)

    progress_bar = ProgressIndicator(len(feature['elements']), usName + ' - Importing', 'scenarios', 50)

    for scenario in feature['elements']:

        progress_bar.update_progress()

        description = scenario['name']
        tcJson = {
            "name": description,
            "testCaseType": "StructuredTestCase",
            "userStoryId": usId,
            "customTestSequenceTitles": ['Given', 'When', 'Then']
        }
        test_case_id = tbcs.post_test_case(pid, tcJson)

        step_List: dict = tbcs_utils.get_sections(logger, tbcs, pid, test_case_id)

        count_created = count_created + 1

        tcJson = {}
        if cfId >= 0:
            tcJson["customFields"] = [{"customFieldId": cfId, "value": "Behave"}]
        tcJson['toBeReviewed'] = True
        tcJson['isAutomated'] = True
        tbcs.patch_test_case(pid, test_case_id, tcJson)

        for steps in scenario["steps"]:
            dest_block = step_List['Given']  # ID of section for GIVEN
            if steps["step_type"] == "when":
                dest_block = step_List['When']  # ID of section for WHEN
            if steps["step_type"] == "then":
                dest_block = step_List['Then']  # ID of section for THEN

            if use_KDT:
                parlist = []
                for par in steps['match']['arguments']:
                    parlist.append({"name": par['name']})

                keywordId = tbcs_utils.get_or_create_kwd(logger, tbcs, pid, {
                    "name": steps["name"],
                    "description": "from BDT",
                    "parlist": parlist
                })['id']

                test_step_Id = tbcs.add_test_step(pid,
                                                  test_case_id,
                                                  steps["name"],
                                                  dest_block,
                                                  "Keyword",
                                                  kwdId=keywordId)
                kwd = tbcs.get_keyword(pid, keywordId)
                for par in steps['match']['arguments']:
                    kwdId = ""
                    for kwdPars in kwd['parameters']:
                        if kwdPars['name'] == par['name']:
                            kwdId = kwdPars['id']
                            continue
                    if kwdId != "":
                        tbcs.update_kwd_par_value(pid, test_case_id, test_step_Id, kwdId, par['value'])

            else:
                tbcs.add_test_step(pid, test_case_id, steps["name"], dest_block)

        logger.debug("Adding Test Case (Scenario): " + description)
    print()

print("\n" + str(count_created) + " Test Cases have been imported.\n")

if config.BEHAVE["cleanup"]:
    os.remove(outFile)
