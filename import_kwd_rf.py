import json
import os
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
plist = tbcs_utils.handle_default_args(config.ACCOUNT, parser)

filename = plist.source[0]
outFile = config.ROBOT_KDT['base_dir'] + \
    config.ROBOT_KDT['script_dir'].replace("\\", "/") + "/out.txt"

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
progress_bar = ProgressIndicator(len(obj["keywords"]), 'Importing', 'Keywords', 50)

for keyword in obj["keywords"]:
    count = count + 1
    progress_bar.update_progress()

    name = keyword["name"]
    lib = keyword["source"]
    description = keyword["doc"]

    logger.debug("Creating Keyword: " + name)

    par_kwd = {}
    par_kwd["name"] = name
    par_kwd["description"] = description[:3998]  # truncate to 3999 chars
    par_kwd["parlist"] = keyword["args"]

    kwd_id = tbcs_utils.get_or_create_kwd(logger, tbcs, pid, par_kwd)['id']

    # after creation, update Keyword with those details we cannot provide while creating
    par_kwd = {}
    if type == "RESOURCE":
        par_kwd["library"] = "resource:" + os.path.basename(lib)
    else:
        par_kwd["library"] = "library:" + filename
    par_kwd["isImplemented"] = True
    tbcs.update_keyword(pid, kwd_id, par_kwd)

    logger.debug("Creation/Match id: " + kwd_id)

ProgressIndicator.clear_indicators()

logger.info(f'Sucessfully imported {str(count)} Keywords.')

if config.ROBOT_KDT["cleanup"]:
    os.remove(outFile)
