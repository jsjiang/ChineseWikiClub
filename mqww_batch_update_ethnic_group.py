import os
import sys

from csv import DictReader
from csv import DictWriter
from pathlib import Path
from pathlib import PurePosixPath

import pywikibot

pywikibot.config.put_throttle = 0

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

# edit reference for ethnic group "P172" 
# when P172 has the value from our batch update list
# add "sated_in" MQWW if the reference is not exist  
stated_in="P248"
mqww_db="Q111326267"

# input file header: property names
# input file data: property values in Q number or string
input_file = Path(os.getcwd()).joinpath("./indata/mqww_wiki_cbdb_batch_update_20220208.csv")
line_no = 1
with open(input_file, 'r', newline='', encoding="utf-8-sig") as csvfile:
    reader = DictReader(csvfile)

    for row in reader:
        line_no +=1
        print("line_no: ",line_no)
        print(row)
        qid = row.get("qid")
        poetID = row.get("poetID")
        cbdb_id = row.get("CBDB_ID")
        if not qid:
            continue

        print("Edit item: ", qid)
        item = pywikibot.ItemPage(repo, qid)
        claims = item.get()["claims"]
        #print(claims)

        for prop, val in row.items():
            if not val:
                continue
            if prop == "P172":
                ref_url = None
                new_val = True
                if prop in claims:
                    for claim in claims[prop]:
                        target = claim.getTarget()
                        current_val = None
                        try:
                            current_val = target.id
                        except Exception:
                            try:
                                current_val = target.text
                            except Exception:
                                try:
                                    current_val = str(target.year)
                                except Exception:
                                    current_val = target

                        if current_val == val:
                            print("Adding Ref state in mqww_db {} for prop: {}, val: {}".format(mqww_db, prop, val)) 
                            ref = pywikibot.Claim(repo, stated_in)
                            ref.setTarget(pywikibot.ItemPage(repo, mqww_db))
                            try:
                                claim.addSources([ref], summary=u'Adding stated in reference')
                            except Exception as ex:
                                print("Error: {}".format(ex))
                            break 


