import argparse
import os

import elasticsearch
import time
import YouTubeApiData
from util import Resources
import YoutubeSerializer
import LoadElastic


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
            index_id = h['_id']
            additional_fields = {}
            hit = h['_source']
            performance = Resources.LplPerformance(hit)

            yt = es.search(index='yt-meta', body={'query':
                                                      {'match':
                                                           {'lpl_id': index_id}
                                                       }
                                                  }
                           )

            if yt['hits']['total'] <= 0:

                v = yt_data.full_performance_search(performance)

                if v:
                    for vid in v:
                        performance.add_video(vid,  date_error=lambda x: LoadElastic.lpl_yt_search(es=es, video=x))

                    #     performance.add_video(vid)
                    #     print(vid)
                    # print("\n")
                    # print(Resources.asciify(h['_source']['KEXPTitle']))
                    # i = input("carry on")
                    # if i == "q":
                    #     break

                videos = yt_data.get_videos([v.id for v in performance.videos], True)

                for v in videos:
                    performance.add_video(v, date_error=lambda x: LoadElastic.lpl_yt_search(es=es, video=x))
                    yt_id = v['id']
                    v['lpl_id'] = index_id
                    es.create(index='yt-meta',
                              body=v,
                              doc_type='yt_meta_full',
                              id=yt_id,
                              ignore=[409])
            else:
                for video in yt['hits']['hits']:
                    video = video['_source']
                    performance.add_video(video, date_error=lambda x: LoadElastic.lpl_yt_search(es=es, video=x))

            print("\n")

            if len(performance.videos) <= 0:
                additional_fields["yt_not_found"] = True

            if not performance.artist_id:
                artist_search = performance.artist_search()
                if artist_search:
                    additional_fields["searched_artist_id"] = performance.artist_id
                else:
                    additional_fields["needs_artist_id"] = True
            if not performance.lpl_item_code:
                additional_fields["needs_itemcode"] = True

            if args.media:
                performance.find_file(args.media)
                if not performance.media_location:
                    additional_fields["no_media"] = True
                performance.find_videos()

            if performance.artist_id and performance.lpl_item_code:
                additional_fields["processed"] = True
                for v in performance.videos:
                    serializer.save_performance(performance, v)

            if len(additional_fields) > 0:
                print(additional_fields)
                es.update(index='lpl-data',
                          doc_type='lpl-meta',
                          id=index_id,
                          body={'doc': additional_fields}
                          )

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
