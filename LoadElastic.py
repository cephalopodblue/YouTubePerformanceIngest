from elasticsearch import Elasticsearch


def load_data(host, index_name, data, data_type):
    es = Elasticsearch(host)

    # create index (ignore 'index already exists' error)
    es.indices.create(index_name, ignore=400)

    try:
        for did, item in data.items():
            es.create(index_name, body=item, id=did, doc_type=data_type)
    except AttributeError:
        for item in data:
            es.create(index_name, body=item, doc_type=data_type)