import argparse
import os

import elasticsearch
import time
import YouTubeApiData
from util import Resources
import YoutubeSerializer



def main():

    parser = argparse.ArgumentParser(description='Get metadata from youtube, musicbrainz, and the LPL to construct a dalet-friendly XML.')

    parser.add_argument('output_directory', help="Directory to store output files.")
    parser.add_argument('-host', default=None, help="Elasticsearch host (none for Localhost")
    parser.add_argument('-media', default=None, help="Places to check for media")
    # parser.add_argument('download_directory', help='Directory containing downloaded files.')
    args = parser.parse_args()

    es = elasticsearch.Elasticsearch(args.host)
    store = os.getcwd()
    output = args.output_directory
    yt_data = YouTubeApiData.VideoData(store)

    serializer = YoutubeSerializer.PerformanceSerializer(output)

    response = es.search(
        index='lpl-data',
        body={
            'query': {
                'bool': {
                    'must': [{'match': {'KEXPVideoEditStatus': 'Uploaded'}}],
                    'must_not': [{'match': {'ItemCode': 'None'}}],
                }
            }
        },
        scroll='5m'
    )

    es.indices.create("yt-meta", body={"mappings":
                                                {"yt-full-meta":
                                                     {"properties":
                                                         { "lpl_id": {"type" : "string"} }
                                                    }
                                                 }
                                            },
                      ignore = [400])

    time.sleep(.5)

    hits = len(response['hits']['hits'])
    while hits > 0:
        for h in response['hits']['hits']:
            hit = h['_source']
            performance = Resources.LplPerformance(hit)

            if not performance.artist_id:
                performance.artist_search()

            yt = es.search(index='yt-meta', body={'query':
                                                      {'match':
                                                           {'lpl_id': h['_id']}
                                                       }
                                                  }
                           )

            if yt['hits']['total'] <= 0:

                v = yt_data.full_performance_search(performance)

                if v:
                    for vid in v:
                        performance.add_video(vid)

                videos = yt_data.get_videos([v.id for v in performance.videos], True)

                for v in videos:
                    performance.add_video(v)
                    yt_id = v['id']
                    v['lpl_id'] = h['_id']
                    es.create(index='yt-meta', body=v, doc_type='yt_meta_full', id=yt_id, ignore=[409])
            else:
                for video in yt['hits']['hits']:
                    video = video['_source']
                    performance.add_video(video)

            for v in performance.videos:
                serializer.save_performance(performance, v)

            if args.media:
                performance.find_file(args.media)
                performance.find_videos()
            print(Resources.asciify(h['_source']['KEXPTitle']))
            print("\n")
            # print(v)

        response = es.scroll(scroll_id=response['_scroll_id'], scroll='5m')
        hits = len(response['hits']['hits'])
        i = input("carry on")
        if i == "q":
            break



if __name__ == "__main__":
    main()
