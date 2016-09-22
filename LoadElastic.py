

def load_data(es, index_name, data, data_type, data_mapping=None):
    # create index (ignore 'index already exists' error)
    if es.indices.exists(index_name):
        es.indices.delete(index_name)
    
    es.indices.create(index_name,
                      body=data_mapping)

    try:
        for did, item in data.items():
            es.create(index_name, body=item, id=did, doc_type=data_type)
    except AttributeError:
        for item in data:
            es.create(index_name, body=item, doc_type=data_type)


def yt_lpl_search(es, lpl_id):
    yt = es.search(index='yt-meta', body={'query':
                                              {'match':
                                                   {'lpl_id': lpl_id}
                                               }
                                          }
                   )
    return yt


def lpl_yt_search(es, video):
    # search for the lpl data that corresponds to the given video's artist name and recording date

    data = es.search(index='lpl-data', body={'query':
                                                      {'bool':
                                                           {'must':
                                                                [{'match': {'KEXPArtistCredit':
                                                                                {'query': video.artist, 'operator': 'and'}}},
                                                                 {'match': {'KEXPDateRecorded': video.recorded}}]
                                                            }
                                                       }
                                                  }
                          )
    return data
