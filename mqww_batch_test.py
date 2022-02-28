import os
import sys

from csv import DictReader
from csv import DictWriter
from pathlib import Path
from pathlib import PurePosixPath

import pywikibot

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

property_list = [
"P106",
"P101",
"P103",
"P1412",
"P1559",
"P1787",
"P1782",
"P21",
"P172",
"P569",
"P570",
"P27"]

# input file header: property names
# input file data: property values in Q number or string
input_file = Path(os.getcwd()).joinpath("./indata/batch_test.csv")
with open(input_file, 'r', newline='', encoding="utf-8-sig") as csvfile:
    reader = DictReader(csvfile)

    for row in reader:
        print(row)
        qid = row.get("qid")
        if not qid:
            continue

        print("Edit item: ", qid)
        item = pywikibot.ItemPage(repo, qid)
        claims = item.get()["claims"]
        #print(claims)

        for prop, val in row.items():
            if not val:
                continue
            if prop in property_list:
                new_val = True
                if prop in claims:
                    print("claim exists: add additional value if it is new - p: {} val: {}".format(prop, val))
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

                        print(type(target))
                        print(current_val)
                        if current_val == val:
                            new_val = False
                            break

                print("new val? ", new_val)

                if new_val:
                    print("add new claim - p: {} val: {}".format(prop, val))
                    claim = pywikibot.Claim(repo, prop)
                    if prop in ['P1559']:
                        target = pywikibot.WbMonolingualText(val, 'zh-hant')
                    elif prop in ['P1787', 'P1782']:
                        target = val
                    elif prop in ['P569', 'P570']:
                        target = pywikibot.WbTime(year=int(val))
                    else:
                        target = pywikibot.ItemPage(repo, val)

                    claim.setTarget(target)
                    item.addClaim(claim, summary=u'Adding a statement')

                    if prop in ['P1787', 'P1782']:    # add qualifier
                        qualifier = pywikibot.Claim(repo, "P282")     # writing system
                        target = pywikibot.ItemPage(repo, "Q178528")  # traditional Chinese characters
                        qualifier.setTarget(target)
                        claim.addQualifier(qualifier, summary=u'Adding a qualifier.')




#claim = pywikibot.Claim(repo, u'P21') #sex or gender
#target = pywikibot.ItemPage(repo, u"Q6581097") # male
#claim.setTarget(target) #Set the target value in the local object.
#item.addClaim(claim, summary=u'Adding gender claim ')


#claim = pywikibot.Claim(repo, u'P1559') #name in native language
#target = pywikibot.WbMonolingualText(u'甘立媃', 'zh-hant')
#claim.setTarget(target) #Set the target value in the local object.
#item.addClaim(claim, summary=u'Adding name in native language claim')
