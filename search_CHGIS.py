import os
import sys

from csv import DictReader
from csv import DictWriter
from pathlib import Path
from pathlib import PurePosixPath
import requests
import json
import csv

url = 'https://maps.cga.harvard.edu/tgaz/placename/json/hvd_'
# input file columns: 'x_coord', 'y_coord', 'CHGIS_PT_ID'
#filename = "test_ids.csv"
filename = "chgis_ids.csv"
input_filename = Path(os.getcwd()).joinpath("./indata/", filename)

# output file
OUTPUT_FIELDNAMES = [
    "cbdb_x_coord",
    "cbdb_y_coord",
    "CHGIS_PT_ID",
    "sys_id",
    "uri",
    "traditional Chinese",
    "simplified Chinese",
    "Pinyin",
    "feature_type_name",
    "feature_type_alternate_name",
    "feature_type_eng",
    "temporal_begin",
    "temporal_end",
    "x_latitude",
    "y_longitude",
    "present_location",
    "historical_context_part_of",
    "historical_context_sub_units",
    "historical_context_preceded_by",
    "data source",
    "source note",
]
output_filename = Path(os.getcwd()).joinpath("./output/", "output_" + filename)
output_file = open(output_filename, 'w', newline='', encoding='UTF-8')
writer = DictWriter(output_file, fieldnames=OUTPUT_FIELDNAMES)
writer.writeheader()

with open(input_filename, 'r', newline='', encoding="utf-8-sig") as csvfile:
    reader = DictReader(csvfile, delimiter='\t')

    line_cnt = 0
    for row in reader:
        line_cnt += 1
        id = row['CHGIS_PT_ID']
        if id:
            print("Retrieving CHGIS ID={}".format(id))
            x = requests.get(url + id)
            if x.status_code == 200:
                try:
                    #data = x.json()
                    data = json.loads(x.text, strict=False)
                    output_row = {
                        "cbdb_x_coord": row["x_coord"],
                        "cbdb_y_coord": row["y_coord"],
                        "CHGIS_PT_ID": id,
                        "sys_id": data.get("sys_id"),
                        "uri": data.get("uri", ''),
                        "feature_type_name": data.get("feature_type").get("name"),
                        "feature_type_alternate_name": data.get("feature_type").get("alternate name"),
                        "feature_type_eng": data.get("feature_type").get("English"),
                        "temporal_begin": data.get("temporal").get("begin"),
                        "temporal_end": data.get("temporal").get("end"),
                        "x_latitude": data.get("spatial").get("latitude"),
                        "y_longitude": data.get("spatial").get("longitude"),
                        "present_location": data.get("spatial").get("present_location"),
                        "historical_context_part_of": data.get("historical_context").get("part of"),
                        "historical_context_sub_units": data.get("historical_context").get("subordinate units"),
                        "historical_context_preceded_by": data.get("historical_context").get("preceded by"),
                        "data source": data.get("data source"),
                        "source note": data.get("source note"),
                    }
                    for item in data.get("spellings"):
                        if item.get("script"):
                            output_row[item.get("script")] = item.get("written form")
                        if item.get("transcribed in"):
                            output_row[item.get("transcribed in")] = item.get("written form")

                    writer.writerow(output_row)
                except Exception as ex:
                    print("JSON Error", ex)
                    print(x.text)
                    continue
            else:
                print("API Request errori. Error code {}".format(x.status_code))


output_file.close()

print("Processed {} lines".format(line_cnt))
print("Output is saved in {}".format(output_filename))

