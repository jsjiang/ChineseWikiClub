import os
import sys

import time
from datetime import date

from csv import DictReader
from csv import DictWriter
from pathlib import Path
from pathlib import PurePosixPath
import json
import chinese_converter as CC

import pywikibot

pywikibot.config.put_throttle = 0

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

def define_label_and_description(row):
    present_location = json.loads(row['present_location'])["text"]
    present_location_hant = CC.to_traditional(present_location)

    labels = {
            "en": row["Pinyin"],
            "zh-hant": row["traditional Chinese"],
            "zh-hans": row["simplified Chinese"],
            "zh": row["simplified Chinese"]
        }
    descriptions = {
             "en": "ancient county of China",
             "zh-hant": "中國歷史地名",
             "zh-hans": "中国历史地名",
             "zh": "中国历史地名"
        }
    if row["feature_type_eng"] != "county":
        descriptions["en"] = ""
    if present_location:
        descriptions["zh-hant"] += ", " + present_location_hant
        descriptions["zh-hans"] += ", " + present_location
        descriptions["zh"] += ", " + present_location

    return labels, descriptions

def update_item(repo, item_id, row):
    item = pywikibot.ItemPage(repo, item_id)
    claims = item.get()["claims"]
    #print(claims)

    # check  if wiki item matches input data
    item_label = item.get()['labels']['en']
    if item_label != row["Pinyin"]:
         print("Matching error: lable of inquery Q {} doesn't match wiki {}/{}".format(item_id,row["Pinyin"], item_label))
         return
 
    # update label  and description
    label_dict, desc_dict = define_label_and_description(row)
    item.editLabels(labels=label_dict, summary="Updating labels.")
    item.editDescriptions(desc_dict, summary="Updating descriptions.")

    # instance of (P31)     ancient county of China (Q28739697)
    # official name (P1448) xx

    if row["feature_type_eng"] == "county" and 'P31' not in claims:
        claim = pywikibot.Claim(repo, u'P31')
        target = pywikibot.ItemPage(repo, u"Q28739697")
        claim.setTarget(target)
        item.addClaim(claim, summary=u"Adding instance of")

    if 'P1448' in claims:
        claim = item.claims['P1448'][0]

        ref = pywikibot.Claim(repo, u'P854')  # Reference URL
        ref.setTarget(row["uri"])

        today = date.today()
        retrieved = pywikibot.Claim(repo, u'P813') #retrieved (P813). Data type: Point in time
        dateCre = pywikibot.WbTime(year=int(today.strftime("%Y")), month=int(today.strftime("%m")), day=int(today.strftime("%d"))) #retrieved -> %DATE TODAY%. Example retrieved -> 29.11.2020
        retrieved.setTarget(dateCre) #Inserting value

        claim.addSources([ref, retrieved], summary=u'Adding reference URL')



# main
input_filename = Path(os.getcwd()).joinpath("./indata/Batch_update_locations.csv")
line_no = 1
with open(input_filename, 'r', newline='', encoding="utf-8-sig") as csvfile:
    reader = DictReader(csvfile)

    for row in reader:
        line_no +=1
        print("line_no: ",line_no)
        print("Update Q No: {}".format(row['Q_No']))
        update_item(repo, row['Q_No'], row)



