import os
import sys

import time
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

def create_item(site, label_dict, desc_dict):
    new_item = pywikibot.ItemPage(site)
    new_item.editLabels(labels=label_dict, summary="Setting labels")
    new_item.editDescriptions(desc_dict, summary="Setting new descriptions.")
    return new_item.getID()

def update_item(repo, item_id, row):
    item = pywikibot.ItemPage(repo, item_id)
    claims = item.get()["claims"]
    #print(claims)

    # add core statements
    # instance of (P31)     ancient county of China (Q28739697)
    # country (P17) china (Q29520)
    # official name (P1448) xx
    # native label (p1705)  xx
    # coordinate location (P625)    xx
    # CHGIS ID (P4711)      xx
    # located in time zone (P421)    UTC+08:00

    if row["feature_type_eng"] == "county":
        claim = pywikibot.Claim(repo, u'P31')
        target = pywikibot.ItemPage(repo, u"Q28739697")
        claim.setTarget(target)
        item.addClaim(claim, summary=u"Adding instance of")

    claim = pywikibot.Claim(repo, u'P17') 
    target = pywikibot.ItemPage(repo, u"Q29520") 
    claim.setTarget(target)
    item.addClaim(claim, summary=u"Adding country")

    claim = pywikibot.Claim(repo, u'P1448')
    target = pywikibot.WbMonolingualText(row["traditional Chinese"], 'zh-hant')   
    claim.setTarget(target)
    item.addClaim(claim, summary=u"Adding official name")
    # add time period
    qualifier = pywikibot.Claim(repo, "P580")     # start time
    target = pywikibot.WbTime(year=int(row["temporal_begin"]))
    qualifier.setTarget(target)
    claim.addQualifier(qualifier, summary=u'Adding a qualifier start time.')
    qualifier = pywikibot.Claim(repo, "P582")     # end time
    target = pywikibot.WbTime(year=int(row["temporal_end"]))
    qualifier.setTarget(target)
    claim.addQualifier(qualifier, summary=u'Adding a qualifier start time.')

    claim = pywikibot.Claim(repo, u'P1705')
    target = pywikibot.WbMonolingualText(row["traditional Chinese"], 'zh-hant')   
    claim.setTarget(target)
    item.addClaim(claim, summary=u"Adding native label")

    lat=float(row["y_latitude"])
    lon=float(row["x_longitude"])
    ref_url = row["uri"]
    claim  = pywikibot.Claim(repo, u'P625') #Adding coordinate location (P625)
    coordinate = pywikibot.Coordinate(lat=lat, lon=lon, precision=0.001) #With location markes
    claim.setTarget(coordinate)
    item.addClaim(claim, summary=u'Adding coordinate claim')

    ref = pywikibot.Claim(repo, u'P854')  # Reference URL
    ref.setTarget(ref_url)
    claim.addSources([ref], summary=u'Adding reference URL')

    claim = pywikibot.Claim(repo, u'P4711')
    claim.setTarget(row["CHGIS_PT_ID"])
    item.addClaim(claim, summary=u"Adding CHGIS ID")

    claim = pywikibot.Claim(repo, u'P421')
    target = pywikibot.ItemPage(repo, u"Q6985")
    claim.setTarget(target)
    item.addClaim(claim, summary=u"Adding time zone")


input_filename = Path(os.getcwd()).joinpath("./indata/Batch_create_locations_3.csv")
output_filename = Path(os.getcwd()).joinpath("./indata/Batch_create_locations_output_3.csv")
output = open(output_filename, 'w', newline='')
line_no = 1
with open(input_filename, 'r', newline='', encoding="utf-8-sig") as csvfile:
    reader = DictReader(csvfile)
 
    fieldnames = reader.fieldnames
    print(fieldnames)
    writer = DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        line_no +=1
        print("line_no: ",line_no)
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
        
        print("create new item:")
        print(labels)
        print(descriptions)

        new_item_id = create_item(site, labels, descriptions) 
        print("New Q No: {}".format(new_item_id))

        row['Q_No'] = new_item_id
        writer.writerow(row)

        print("wait 5 sec before updating new item")
        time.sleep(5)
        update_item(repo, new_item_id, row)

output.close()


