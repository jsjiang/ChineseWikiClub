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

def update_item(repo, item_id, claims):
    item = pywikibot.ItemPage(repo, item_id)
    current_claims = item.get()["claims"]
   
    """claims = {
            "P31": ["Q7725634", "Q12106333"], # instance of literary work, poetry collection
            "P1476": title_P1476, 
            "P136": ["Q482", "Q1069928"], # poetry, Chinese poetry
            "P7937": ["Q5185279"], # form or creative work: poem
            "P50": author_P50,
            "P854": ref_url_P854,
            "P495": country_P495, # list of qnums
            "P407": ["Q18130932"],  # language of work: Traditional Chinese
            "P571": inception_P571,
            "P1319": inception_earliest_P1319,
            "P1326": inception_latest_P1326
        }
    """
    claims_with_qids = ["P31", "P136", "P495", "P407"]
    claims_zh_hant = ["P1476"]
    ref_url = claims.get("P854")
    p50_author = claims.get("P50")

    if "P50" not in current_claims and p50_author:
        claim = pywikibot.Claim(repo, u"P50")
        target = pywikibot.ItemPage(repo, p50_author)
        claim.setTarget(target)
        ref = pywikibot.Claim(repo, u'P854')  # Reference URL
        ref.setTarget(ref_url)
        claim.addSources([ref], summary=u'Adding reference URL')
        item.addClaim(claim)

    for key in claims_zh_hant:
        if key not in current_claims and claims.get(key):
            claim = pywikibot.Claim(repo, key)
            target = pywikibot.WbMonolingualText(claims.get(key), 'zh-hant')   
            claim.setTarget(target)
            item.addClaim(claim)

    for key in claims_with_qids:
        if key not in current_claims and claims.get(key):
            for qid in claims.get(key):
                claim = pywikibot.Claim(repo, key)
                target = pywikibot.ItemPage(repo, qid)
                claim.setTarget(target)
                item.addClaim(claim)

    p571 = claims.get("P571")
    p1319 = claims.get("P1319")
    p1326 = claims.get("P1326")
    if "P571" not in current_claims and p571:
        claim = pywikibot.Claim(repo, "P571")
        target = pywikibot.WbTime(year=int(p571))
        claim.setTarget(target)
        ref = pywikibot.Claim(repo, u'P854')  # Reference URL
        ref.setTarget(ref_url)
        claim.addSources([ref], summary=u'Adding reference URL')
        item.addClaim(claim)

        if p1319:
            qualifier = pywikibot.Claim(repo, "P1319")     # start time
            target = pywikibot.WbTime(year=int(p1319))
            qualifier.setTarget(target)
            claim.addQualifier(qualifier)
        if p1326:
            qualifier = pywikibot.Claim(repo, "P1326")     # start time
            target = pywikibot.WbTime(year=int(p1326))
            qualifier.setTarget(target)
            claim.addQualifier(qualifier)
        
        
def get_content_in_parentheses(a_str):
    """note: there might be more than one parentheses
    """
    reversed = a_str[::-1]
    last_left_parenthesis = len(a_str) - reversed.find("(")
    last_right_parenthesis = len(a_str) - reversed.find(")")
    return a_str[last_left_parenthesis:last_right_parenthesis-1].strip()

get_dynansty_qnum = {
    "Guangxu": ["Q8733"],
    "Min guo": ["Q13426199"],
    "Ming": ["Q9903"],
    "Minguo": ["Q13426199"],
    "QIng": ["Q8733"],
    "Qing": ["Q8733"],
    "Qing Guangxu": ["Q8733"],
    "Qing mo": ["Q8733"],
    "Qing mo Min chu": ["Q8733", "Q13426199"],
    "Xuantong": ["Q8733"],
    "清": ["Q8733"]
}

mqww_work_url = "https://digital.library.mcgill.ca/mingqing/search/details-work.php"

input_filename = Path(os.getcwd()).joinpath("./indata/poet_with_Q_work_230220709_flagged_first_2-5.csv")
output_filename = Path(os.getcwd()).joinpath("./indata/poet_with_Q_work_230220709_output_first_2-5.csv")
item_filename = Path(os.getcwd()).joinpath("./indata/poet_with_Q_work_230220709_item_first_2-5.csv")

output = open(output_filename, 'w', newline='')
items = open(item_filename, 'w', newline='')
items_fieldnames = ["workID", "lables", "descriptions", "claims", "work_qid"]

line_no = 1
with open(input_filename, 'r', newline='', encoding="utf-8-sig") as csvfile:
    reader = DictReader(csvfile)
 
    fieldnames = reader.fieldnames
    fieldnames.append('work_qid')
    print(fieldnames)
    writer = DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    writer_items = DictWriter(items, fieldnames=items_fieldnames)
    writer_items.writeheader()

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
            print(labels)
            print(descriptions)
            continue
        
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

        country_P495 = None
        dateDynansty = row.get("DateDynastyPY")
        if dateDynansty:
            country_P495 = get_dynansty_qnum[dateDynansty]
        if country_P495:
            print(f"dateDynansty: {dateDynansty} - {country_P495}")
            print(ref_url_P854)
        else:
            print("dateDynansty: None")
        
        inception_P571 = row.get("DateXF").strip()
        inception_earliest_P1319 = None
        inception_latest_P1326 = None

        if not inception_P571.isnumeric() or inception_P571 == '0':
            inception_earliest_P1319 = row.get("PubStartYear").strip()
            inception_latest_P1326 = row.get("PubEndYear").strip()

            if not inception_earliest_P1319.isnumeric() or inception_earliest_P1319 == '0':
                inception_earliest_P1319 = None

            if not inception_latest_P1326.isnumeric() or inception_latest_P1326 == '0':
                inception_latest_P1326 = None
            
            inception_P571 = inception_earliest_P1319

            if inception_earliest_P1319 == inception_latest_P1326:
                inception_earliest_P1319 = None
                inception_latest_P1326 = None
        
        if inception_P571 and inception_latest_P1326 == '0':
            inception_P571 = None
        print(f"inception_P571: {inception_P571}")
        
        if inception_earliest_P1319:
            print(f"inception_earliest_P1319: {inception_earliest_P1319}")
        if inception_latest_P1326:
            print(f"inception_latest_P1326: {inception_latest_P1326}")
        print(ref_url_P854)

        claims = {
            "P31": ["Q7725634", "Q12106333"], # instance of literary work, poetry collection
            "P1476": title_P1476, 
            "P136": ["Q482", "Q1069928"], # poetry, Chinese poetry
            "P7937": ["Q5185279"], # form or creative work: poem
            "P50": author_P50,
            "P854": ref_url_P854,
            "P495": country_P495,  # list of qnums
            "P407": ["Q18130932"],  # language of work: Traditional Chinese
            "P571": inception_P571,
            "P1319": inception_earliest_P1319,
            "P1326": inception_latest_P1326
        }

        print(claims)

        new_item_id = create_item(site, labels, descriptions)
        print("New Q No: {}".format(new_item_id))

        row['work_qid'] = new_item_id
        writer.writerow(row)

        items_row = {
            "workID": work_id,
            "lables": labels,
            "descriptions": descriptions,
            "claims": claims,
            "work_qid": new_item_id
        }
        writer_items.writerow(items_row)

        print("wait 5 sec before updating new item")
        time.sleep(5)
        update_item(repo, new_item_id, claims)
        print(f"updating new item {new_item_id} completed.")

output.close()
items.close()


