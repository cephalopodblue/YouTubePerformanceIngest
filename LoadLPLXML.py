import xml.etree.ElementTree as etree
import argparse
from elasticsearch import Elasticsearch
import LoadElastic

mapping_name = "lpl-meta"

lpl_data_map = {"dynamic": "false",
               "properties":
                   {"ItemCode": {"type": "string"},
                    "title": {"type": "string"},
                    "KEXPArtist": {"type": "string"},
                    "KEXPArtistCredit": {"type": "string"},
                    "KEXPDateRecorded": {"type" : "date",
                                         "format" : "strict_date_optional_time||epoch_millis"},
                    "KEXPLivePerformanceSerialID": {"type": "integer"},
                    "KEXPTitle": {"type": "string"},
                    "KEXPTotalTracks": {"type": "integer"},
                    "KEXPTrack01": {"type": "string"},
                    "KEXPTrack02": {"type": "string"},
                    "KEXPTrack03": {"type": "string"},
                    "KEXPTrack04": {"type": "string"},
                    "KEXPTrack05": {"type": "string"},
                    "KEXPTrack06": {"type": "string"},
                    "KEXPTrack07": {"type": "string"},
                    "KEXPTrack08": {"type": "string"},
                    "KEXPTrack09": {"type": "string"},
                    "KEXPTrack10": {"type": "string"},
                    "KEXPTrack11": {"type": "string"},
                    "KEXPTrack12": {"type": "string"},
                    "KEXPTrack13": {"type": "string"},
                    "KEXPTrack14": {"type": "string"},
                    "KEXPTrack15": {"type": "string"},
                    "KEXPTrack16": {"type": "string"},
                    "KEXPTrack17": {"type": "string"},
                    "KEXPTrack18": {"type": "string"},
                    "KEXPTrack19": {"type": "string"},
                    "KEXPTrack20": {"type": "string"},
                    "KEXPVideoEditStatus": {"type": "string"},
                    "needs_artist_id": {"type": "boolean"},
                    "needs_itemcode": {"type": "boolean"},
                    "media_not_found": {"type": "boolean"},
                    "processed": {"type": "boolean"},
                    "searched_artist_id": {"type": "string"},
                    "yt_not_found": {"type": "boolean"}
                    }}


def load_lpl_data_xml():
    parser = argparse.ArgumentParser(description='Load XML-formatted LPL data into an elasticsearch index.')

    parser.add_argument('xml_file', help="File containing LPL xml.")
    parser.add_argument('-host', default=None, help="Elasticsearch host (none for Localhost")

    args = parser.parse_args()

    data = {}
    tree = etree.parse(args.xml_file)
    root = tree.getroot()

    for child in root:
        performance = {}
        for i in child:
            if i.tag in lpl_data_map['properties'].keys():
               performance[i.tag] = i.text
        data[child.find("KEXPLivePerformanceSerialID").text] = performance

    es = Elasticsearch(args.host)
    LoadElastic.create_index(es, "lpl-data", {mapping_name: lpl_data_map})
    LoadElastic.load_data(es, "lpl-data", data, mapping_name)


if __name__ == "__main__":
    load_lpl_data_xml()