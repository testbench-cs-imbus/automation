import json
import os
import re
import subprocess
import argparse

import config
import utils.logger_utils as logger_utils
import utils.tbcs_utils as tbcs_utils
from utils.terminal_utils import ProgressIndicator

# Configure logging
logger = logger_utils.get_logger('import Keywords from RF', config.LOGLEVEL)

# Parse command line
parser = argparse.ArgumentParser(description="Import Keywords from Robot Framework ressource file or library.")
parser.add_argument('source', nargs=1, help='name of file or folder to be scanned')
parser.add_argument('-x', '--prefix', nargs=1, help='prefix added to each Keyword name')
parser.add_argument('-d',
                    '--update',
                    dest='update',
                    action='store_const',
                    const=True,
                    default=False,
                    help='upDate existing Keywords')
plist = tbcs_utils.handle_default_args(config.ACCOUNT, parser)

filename = plist.source[0]
outFile = config.ROBOT_KDT['base_dir'] + \
    config.ROBOT_KDT['script_dir'].replace("\\", "/") + "/out.txt"

prefix = ""
if plist.prefix != None:  # each Keyword will get this prefix
    prefix = plist.prefix[0] + "."

if plist.update == True:
    updateFlag = 2
else:
    updateFlag = 0

call = ["libdoc", "-f", "json", filename, outFile]
try:
    subprocess.run(call, check=True)
except:
    logger.error("Calling 'libdoc' failed - is it set up correctly? Name of file correct? Terminating ...")
    exit(1)

with open(outFile, 'r') as file:
    obj = json.load(file)

# outFile is always written, check for found keywords
if len(obj["keywords"]) == 0:
    logger.error(f'No keywords found in the given source: {filename}. Possibly the file or library does not exist.')
    exit(1)

type = obj["type"]
logger.info(f'Found {len(obj["keywords"])} Keywords from source of type "{type}"')

logger.info("Starting import ...")

# connect to iTB and select product to write in
tbcs = tbcs_utils.connect_itb(logger, config.ACCOUNT)

pid = tbcs_utils.ask_for_product(logger, tbcs)
if (pid == ""):
    exit()

count = 0
reuse_count = 0
update_count = 0

progress_bar = ProgressIndicator(len(obj["keywords"]), 'Importing', 'Keywords', 50)

for keyword in obj["keywords"]:
    progress_bar.update_progress()

    name = keyword["name"]
    lib = keyword["source"]
    description = keyword["doc"]

    logger.debug("Creating Keyword: " + name)

    par_kwd = {}

    par_kwd["name"] = prefix + name
    par_kwd["description"] = description[:3998]  # truncate to 3999 chars

    # handle parameter descriptions: works for _some_ RF-libs, e.g. Browser
    re_parameter = re.compile(r"\<p\>\<code\>(.*?)\<\/code\>(.*?)\<\/p\>")

    #kwd_struct = tbcs.get_keyword(pid, kwd_id)
    for match in re_parameter.finditer(description):
        match_name = match.group(1)
        match_desc = match.group(2)

        for kwd_rf in keyword['args']:
            if match_name == kwd_rf['name']:
                kwd_rf['description'] = match_desc

    # < handle ...

    par_kwd["parlist"] = keyword["args"]
    result = tbcs_utils.get_or_create_kwd(logger, tbcs, pid, par_kwd, True, updateFlag)

    # collect some information we either use to update the new KWD, or we use to figure out if we need to update an existing KWD
    kwd_id = result['id']
    kwd_struct = tbcs.get_keyword(pid, kwd_id)

    # after creation or update, update Keyword with those details we cannot provide while creating
    par_kwd = {}
    if type == "RESOURCE":
        par_kwd["library"] = "resource:" + os.path.basename(lib)
    else:
        par_kwd["library"] = "library:" + filename
    par_kwd["isImplemented"] = True

    # update kwd attributes
    update_attributes = False
    if (par_kwd["library"] != kwd_struct['library'] or kwd_struct['isImplemented'] == False) and updateFlag > 0:
        update_attributes = True

    if result['action'] == 'created' or result['action'] == 'updated' or update_attributes == True:
        tbcs.update_keyword(pid, kwd_id, par_kwd)

    # handle parameter list
    re_parameter = re.compile(r"\<p\>\<code\>(.*?)\<\/code\>(.*?)\<\/p\>")
    lut = {}

    if result['action'] == 'created' or result['action'] == 'updated':  # 1st case: normal create/update
        for par_info in kwd_struct['parameters']:
            lut[par_info['name']] = par_info['id']

        for match in re_parameter.finditer(description):
            if match.group(1) in lut.keys():
                tbcs.update_keyword_parameter(pid, lut[match.group(1)], {'paramDescription': match.group(2)})

    else:  # 2nd case: update kwd par desc only
        if updateFlag > 0:
            for par_info in kwd_struct['parameters']:
                lut[par_info['name']] = par_info['id']

            for match in re_parameter.finditer(description):
                if match.group(1) in lut.keys():
                    for par_info in kwd_struct['parameters']:
                        if par_info['name'] == match.group(1):
                            if par_info['description'].strip() != match.group(2).strip():
                                print(f'Kwd <{name}>: Par description updated <{par_info["name"]}>')
                                result['action'] = 'updated'
                                tbcs.update_keyword_parameter(pid, lut[match.group(1)],
                                                              {'paramDescription': match.group(2)})
                            #else:
                            # print(f'par description unchanged {par_info["name"]}')

    if result['action'] == 'created':
        count = count + 1
        logger.debug(f'Keyword created: {prefix + name}')
    else:
        if result['action'] == 'updated' or update_attributes == True:
            update_count = update_count + 1
            logger.debug(f'Keyword updated: {prefix + name}')
        else:
            reuse_count = reuse_count + 1
            logger.debug(f'Keyword not imported: {prefix + name} - reason: {result["action"]}')

    logger.debug("Creation/Update id: " + kwd_id)

ProgressIndicator.clear_indicators()

logger.info(f'Sucessfully imported {str(count)} Keywords.')
if (update_count > 0):
    logger.info(f'Updated {str(update_count)} existing Keywords.')
if (reuse_count > 0):
    logger.info(f'Found {str(reuse_count)} existing Keywords - not importing them.')

if config.ROBOT_KDT["cleanup"]:
    os.remove(outFile)
