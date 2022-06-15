import os
import subprocess
import re
import argparse

import config
import utils.logger_utils as logger_utils
import utils.tbcs_utils as tbcs_utils
from utils.terminal_utils import ProgressIndicator

# Parse command line
parser = argparse.ArgumentParser(description="Import BDT steps via behave.")
parser.add_argument('source', nargs=1, help='name of feature file (*.feature) or folder to be scanned')
parser.add_argument('-x', '--praefix', nargs=1, help='praefix added to each Keyword name')
plist = tbcs_utils.handle_default_args(config.ACCOUNT, parser)

# Configure logging
logger = logger_utils.get_logger('import BDT Steps', config.LOGLEVEL)

filename = plist.source[0].replace("\\", "/")
outFile = config.BEHAVE['base_dir'] + config.BEHAVE['scenario_dir'].replace("\\", "/") + "/out.txt"

praefix = ""
if plist.praefix != None:  # each Keyword will get this praefix
    praefix = plist.praefix[0] + "."

call = ["behave", "-d", "-f", "steps.doc", "-o", outFile]
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

file = open(outFile, 'r')
lines = file.readlines()
file.close()

re_line = re.compile(r"@(.*)\(\'(.*?)\'\)")
re_par = re.compile(r"\"\{(.*?)\}\"")
#re_par = re.compile(r"\{(.*?)\}")

count_created = 0
count_reused = 0

progress_bar = ProgressIndicator(len(lines), 'Reading', 'lines', 50)

for current in lines:

    progress_bar.update_progress()

    current = current.strip()
    parameter_list = []
    if len(current) > 1:
        if current[0] == "@":
            match = re_line.search(current)
            if not match:
                continue
            lib = match.group(1)
            name = match.group(2)
            par_match = re_par.search(name)

            while par_match != None:
                name = name.replace(par_match.group(0), "\"${" + par_match.group(1) + "}\"")
                parameter_list.append({"name": par_match.group(1)})
                par_match = re_par.search(name)

            description = "Import from Behave."

            logger.debug("Creating Keyword: " + name)

            par_kwd = {}

            par_kwd["name"] = praefix + name
            par_kwd["description"] = description[:3998]  # truncate to 3999 chars
            par_kwd["parlist"] = parameter_list
            result = tbcs_utils.get_or_create_kwd(logger, tbcs, pid, par_kwd)
            kwd_id = result['id']

            if result['action'] == 'created':
                # after creation, update Keyword with those details we cannot provide while creating
                par_kwd = {}
                par_kwd["isImplemented"] = True
                par_kwd["library"] = lib.upper()

                tbcs.update_keyword(pid, kwd_id, par_kwd)

                count_created = count_created + 1
            else:
                count_reused = count_reused + 1

            logger.debug("Creation/Match id: " + kwd_id)

logger.info(f"{str(count_created)} Keywords imported.")
if count_reused > 0:
    logger.info(f"{str(count_reused)} more Keywords not imported since they existed already.")

if config.BEHAVE["cleanup"]:
    os.remove(outFile)
