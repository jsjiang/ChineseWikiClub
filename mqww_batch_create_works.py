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

def get_content_in_parentheses(a_str):
    """note: there might be more than one parentheses
    """
    reversed = a_str[::-1]
    last_left_parenthesis = len(a_str) - reversed.find("(")
    last_right_parenthesis = len(a_str) - reversed.find(")")
    return a_str[last_left_parenthesis:last_right_parenthesis-1].strip()

get_dynansty_qnum = {
    "Guangxu": "Q8733",
    "Min guo": "Q13426199",
    "Ming": "Q9903",
    "Minguo": "Q13426199",
    "QIng": "Q8733",
    "Qing": "Q8733",
    "Qing Guangxu": "Q8733",
    "Qing mo": "Q8733",
    "Qing mo Min chu": "Q8733，Q13426199：how to handle two",
    "Xuantong": "Q8733",
    "清": "Q8733"
}

mqww_work_url = "https://digital.library.mcgill.ca/mingqing/search/details-work.php"

input_filename = Path(os.getcwd()).joinpath("./indata/poet_with_Q_work_230220709_flaged.csv")
output_filename = Path(os.getcwd()).joinpath("./indata/poet_with_Q_work_230220709_output.csv")
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
        # Yong xue lou gao: 5 juan, juan shou 1 juan, fu 1 juan ( by Gan lirou, Qing dynasty)
        titlePY = row.get('TitlePY')
        # 詠雪樓稿﹕五卷，卷首一卷，附一卷(清甘立媃撰)
        titleHZ = row.get('TitleHZ')
        # replace "（" with "(", "）" with ")";
        # replace "﹕" and "：" with ":"
        titleHZ = titleHZ.replace("（", "(").replace("）", ")").replace("﹕", ":").replace("：", ":")

        label_en = titlePY
        seps = [":", "("]
        for sep in seps:
            x = titlePY.split(sep)
            if len(x) > 1:
                label_en = x[0]
                break

        label_han_t = titleHZ
        label_han_s = ''
        # split by ":" or "﹕", or "："
        seps = [ ":", "("]
        for sep in seps:
            x = titleHZ.split(sep)
            if len(x) > 1:
                label_han_t = x[0]
                break
        
        label_han_s = CC.to_simplified(label_han_t)
        
        # get content in the parentheses ()
        desc_en = get_content_in_parentheses(titlePY)
        desc_en = f"Poetry collection {desc_en}"
        
        desc_han_t = get_content_in_parentheses(titleHZ)
        desc_han_s = CC.to_simplified(desc_han_t)

        labels = {
            "en": label_en,
            "zh-hant": label_han_t,
            "zh-hans": label_han_s,
            "zh": label_han_s
        }
        descriptions = {
             "en": desc_en,
             "zh-hant": desc_han_t,
             "zh-hans": desc_han_s,
             "zh": desc_han_s
        }
        
        if row.get("Flag").lower() == "skip":
            print("Skip this label/desc: dup or already has a Q num")
        else:
            print("create new item label/desc:")
        print(labels)
        print(descriptions)
 
        title_P1476  = label_han_t
        print(f"title_P1476:{title_P1476}")
        print("add Language (mandatory): Traditional Chinese")

        work_id = row.get("workID")
        author_P50 = row.get("qid")
        ref_url_P854 = f"{mqww_work_url}?workID={work_id}&language=eng"

        print(f"author_P50: {author_P50}")
        print(f"work_id: {work_id}")
        print(ref_url_P854)

        country_p495 = None
        dateDynansty = row.get("DateDynastyPY")
        if dateDynansty:
            country_p495 = get_dynansty_qnum[dateDynansty]
        if country_p495:
            print(f"{dateDynansty} - {country_p495}")
            print(ref_url_P854)
        else:
            print("dateDynansty: None")
        

        inception_p571 = row.get("DateXF")
        inception_earliest_p1319 = None
        inception_latest_p1326 = None
        if len(inception_p571) > 4:
            inception_p571 = row.get("PubStartYear")
            inception_earliest_p1319 = row.get("PubStartYear")
            inception_latest_p1326 = row.get("PubEndYear")
        print(f"inception_p571: {inception_p571}")
        if inception_earliest_p1319:
            print(f"inception_earliest_p1319: {inception_earliest_p1319}")
        if inception_latest_p1326:
            print(f"inception_latest_p1326: {inception_latest_p1326}")
        print(ref_url_P854)

        #new_item_id = create_item(site, labels, descriptions) 
        #print("New Q No: {}".format(new_item_id))

        #row['Q_No'] = new_item_id
        #writer.writerow(row)

        #print("wait 5 sec before updating new item")
        #time.sleep(5)
        #update_item(repo, new_item_id, row)

print("#### entries for all ###")
print("instance of (P31): literary work (Q7725634)")
print("instance of (P31): poetry collection (Q12106333)")

print("has edition or translation (P747): will be updated later once we create the edition level item")
print("genre (P136): poetry (Q482)")
print("genre (P136): Chinese poetry (Q1069928)")
print("form of creative work (P7937):  poem (Q5185279)")
print("language of work or name (P407)	Traditional Chinese (Q18130932)")

print("Sample work: 樓居小草 https://www.wikidata.org/wiki/Q56653475")

output.close()


