import argparse
from elasticsearch import Elasticsearch
import LoadElastic
import os
import YouTubeApiData

mapping_name = "yt_meta_full"

meta = ["fileDetails", "contentDetails", "status", "snippet"]

yt_data_map = {"dynamic": "false",
               "properties":
                   {"ItemCode": {"type": "string"},
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "lpl_id": {"type": "string"},
                    "fileDetails": {"type": "object"},
                    "contentDetails": {"type": "object"},
                    "status": {"type": "object"},
                    "snippet": {"type": "object"},
                    "date_recorded": {"type": "date",
                                         "format" : "strict_date_optional_time||epoch_millis"},
                    "multiple_performances": {"type": "string"},
                    "processed": {"type": "boolean"},
                    "searched_artist_id": {"type": "string"},
                    }}


def load_yt_data():
    parser = argparse.ArgumentParser(description='Load metadata from YT into an elasticsearch index.')

    parser.add_argument('-host', default=None, help="Elasticsearch host (none for Localhost")

    args = parser.parse_args()

    es = Elasticsearch(args.host)
    
    LoadElastic.create_index(es, "yt-meta", {mapping_name: yt_data_map})
    
    store = os.getcwd()
    yt_data = YouTubeApiData.VideoData(store)

    vid_gen = yt_data.next_videos_meta(meta=meta)
    
    i = 0
    
    for video_list in vid_gen:
        for v in video_list:
            video = {}
            for key, value in v.items():
                if key in yt_data_map["properties"]:
                    video[key] = value
            LoadElastic.load_doc(es, "yt-meta", mapping_name, video, v['id'])
            i += 1
        print(i)



if __name__ == "__main__":
    load_yt_data()