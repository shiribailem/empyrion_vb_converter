# When an object is missing in the new version, replace with this object (based on key)
failkey = 'CG_MoneyCard_Silver'


from sys import argv, stdout
import json
import os
import fnmatch
from datetime import datetime

if len(argv) < 4:
    print("Usage: virtual_backpack_conversion.py old_ids.json new_ids.json directory")
    exit()

def find_json_files(directory):
    json_files = []
    for root, dirs, files in os.walk(directory):
        for filename in fnmatch.filter(files, '*.json'):
            json_files.append(os.path.join(root, filename))
    return json_files

class loggers:
    def __init__(self, filename):
        self.terminal = stdout
        self.log = open(filename, "a")

    def write(self, message):
        self.terminal.write(f"{datetime.now()}: {message}\n")
        self.log.write(f"{datetime.now()}: {message}\n")

    def close(self):
        self.log.close()


newids = {}
oldids = {}


with open(argv[1],'r') as file:
    newids = json.loads(file.read())
with open(argv[2], 'r') as file:
    oldids = json.loads(file.read())

logger = loggers("virtual_backpack_conversion_log.txt")

try:
    failmap = newids[failkey]
except KeyError:
    logger.write("Missing key for failure replace: " + failkey)
    exit()

logger.write("Building conversion table:")
table = {}
faillist = []
success = 0
fail = 0

for key in oldids.keys():
    if key in newids.keys():
        table[oldids[key]] = newids[key]
        success += 1
    else:
        table[oldids[key]] = failmap
        faillist.append(oldids[key])
        logger.write(f"\tMissing: {key}")
        fail += 1

logger.write(f"Success: {success}, Fail: {fail}")

logger.write(f"Finding json files in :{argv[3]}")
files = find_json_files(argv[3])
logger.write(f"Found {len(files)} files")

for filename in files:
    changed = False
    failcount = 0
    with open(filename, 'r') as file:
        try:
            vb = json.loads(file.read())
        except:
            logger.write(f"Failed to load file: {filename}")
            continue
    try:
        bps = vb['Backpacks']
    except KeyError:
        logger.write(f"File {filename} does not have a 'Backpacks' key")
        continue

    fixedbps = []

    for bp in bps:
        itemlist = bp['Items']
        newlist = []

        if itemlist is None:
            logger.write(f"File {filename} has a backpack with no items")
            continue

        for item in itemlist:
                oldid = item['id']
                if item['id'] in faillist:
                    failcount += item['count']
                try:
                    item['id'] = table[item['id']]
                except KeyError:
                    logger.write(f"Failed to convert item: {item}")
                    item['id'] = failmap
                    failcount += item['count']
                if oldid != item['id']:
                    changed = True
                newlist.append(item)

        fixedbps.append({'Items': newlist})

    vb['Backpacks'] = fixedbps

    if changed:
        with open(filename, 'w') as file:
            file.write(json.dumps(vb, indent=2))

        if failcount > 0:
            logger.write(f"Fixed {filename} re-imbursing {failcount} x {failkey}")
        else:
            logger.write(f"Fixed {filename}")
    #else:
        #logger.write(f"No changes to {filename}")

logger.close()
