import os
import json
import requests
import datetime
import jsonpickle
import shutil
import urllib

import elasticsearch.helpers
from elasticsearch import Elasticsearch

from .interfaces import SearchEngineInterface

#from ltr.helpers.handle_resp import resp_msg



def pretty(obj):
    print(jsonpickle.encode(obj,indent=2))

## -------------------------------------------
## Java-Friendly datetime string format

def timestamp():
    return datetime.datetime.now().isoformat() + 'Z'

## -------------------------------------------
## Pass-through query!
## Just take the query as provided, run it against elasticsearch, and return the raw response

def passthrough(uri):
    req = requests.get(uri)
    return req.text,req.status_code




class ElasticResp():
    def __init__(self, resp):
        self.status_code = 400
        if 'acknowledged' in resp and resp['acknowledged']:
            self.status_code = 200
        else:
            self.status_code = resp['status']
            self.text = json.dumps(resp, indent=2)

class BulkResp():
    def __init__(self, resp):
        self.status_code = 400
        if resp[0] > 0:
            self.status_code = 201

class SearchResp():
    def __init__(self, resp):
        self.status_code = 400
        if 'hits' in resp:
            self.status_code = 200
        else:
            self.status_code = resp['status']
            self.text = json.dumps(resp, indent=2)


class Elastic(SearchEngineInterface):

    ## -------------------------------------------
    ## Index Admin
    def indexes(self, kind=None) -> list:
        #List the existing indexes of the given kind
        pass

    def indexExists(self,name: str) -> bool:
        #Returns true if the index exists on the host
        pass

    def indexCreate(self,config: str,timeout=10000) -> bool:
        #Creates a new index with a specified configuration
        pass

    ## -------------------------------------------
    ## Content Update
    def index(self, documents:list, path: str, timeout=10000) -> str:
        #Accepts a skipchunk object to index the required data
        pass

    ## -------------------------------------------
    ## Querying

    def search(self,querystring, handler: str) -> str:
        #Searches the engine for the query
        pass

    ## -------------------------------------------
    ## Graphing

    def aggregateQuery(self,field:str,mincount=1,limit=100) -> dict:
        #Crafts an aggregate to be used by the search engine
        pass

    def parseAggregate(self,field:str,res:dict) -> dict:
        #parses an aggregate resultset normalizing against a generic interface
        pass

    def suggest(self,prefix:str,dictionary="conceptLabelSuggester",count=25,build=False) -> dict:
        #crafts a suggestion query
        pass

    def conceptVerbConcepts(self,concept:str,verb:str,mincount=1,limit=100) -> list:
        # Accepts a verb to find the concepts appearing in the same context
        pass

    def conceptsNearVerb(self,verb:str,mincount=1,limit=100) -> list:
        # Accepts a verb to find the concepts appearing in the same context
        pass

    def verbsNearConcept(self,concept:str,mincount=1,limit=100) -> list:
        # Accepts a concept to find the verbs appearing in the same context
        pass

    def suggestConcepts(self,prefix:str,build=False) -> list:
        # Suggests a list of concepts given a prefix
        pass

    def suggestPredicates(self,prefix:str,build=False) -> list:
        # Suggests a list of predicates given a prefix
        pass

    def summarize(self,mincount=1,limit=100) -> list:
        # Summarizes a core
        pass

    def graph(self,subject:str,objects=5,branches=10) -> list:
        # Gets the subject-predicate-object graph for a subject
        pass

    def explore(self,term,contenttype="concept",build=False,quiet=False,branches=10) -> list:
        # Pretty-prints a graph walk of all suggested concepts and their verbs given a starting term prefix
        pass

    def __init__(self,host,name,kind,path):
        self.host = host
        self.name = name + '-' + kind
        self.kind = kind
        self.path = os.path.abspath(path)

        self.root = os.path.join(self.path, name)
        self.elastic_home = os.path.join(self.root, 'elastic_'+self.kind)
        self.document_data = os.path.join(self.root, 'documents')

        self.elastic_uri = self.host + self.name

"""

    def __init__(self, configs_dir='.'):
        self.docker = os.environ.get('SKIPCHUNK_DOCKER') != None
        self.configs_dir = configs_dir #location of elastic configs

        if self.docker:
            self.host = 'elastic'
        else:
            self.host = 'localhost'

        self.elastic_ep = 'http://{}:9200/_ltr'.format(self.host)
        self.es = Elasticsearch('http://{}:9200'.format(self.host))

    def get_host(self):
        return self.host

    def name(self):
        return "elastic"

    def delete_index(self, index):
        resp = self.es.indices.delete(index=index, ignore=[400, 404])
        resp_msg(msg="Deleted index {}".format(index), resp=ElasticResp(resp), throw=False)


    def create_index(self, index):
        # Take the local config files for Elasticsearch for index, reload them into ES
        cfg_json_path = os.path.join(self.configs_dir, "%s_settings.json" % index)
        with open(cfg_json_path) as src:
            settings = json.load(src)
            resp = self.es.indices.create(index, body=settings)
            resp_msg(msg="Created index {}".format(index), resp=ElasticResp(resp))

    def index_documents(self, index, doc_src):

        def bulkDocs(doc_src):
            for doc in doc_src:
                if 'id' not in doc:
                    raise ValueError("Expecting docs to have field 'id' that uniquely identifies document")
                addCmd = {"_index": index,
                          "_id": doc['id'],
                          "_source": doc}
                yield addCmd

        resp = elasticsearch.helpers.bulk(self.es, bulkDocs(doc_src), chunk_size=100)
        self.es.indices.refresh(index=index)
        resp_msg(msg="Streaming Bulk index DONE {}".format(index), resp=BulkResp(resp))

    def reset_ltr(self, index):
        resp = requests.delete(self.elastic_ep)
        resp_msg(msg="Removed Default LTR feature store".format(), resp=resp, throw=False)
        resp = requests.put(self.elastic_ep)
        resp_msg(msg="Initialize Default LTR feature store".format(), resp=resp)

    def create_featureset(self, index, name, ftr_config):
        resp = requests.post('{}/_featureset/{}'.format(self.elastic_ep, name), json=ftr_config)
        resp_msg(msg="Create {} feature set".format(name), resp=resp)

    def log_query(self, index, featureset, ids, params={}):
        params = {
            "query": {
                "bool": {
                    "filter": [
                        {
                            "sltr": {
                                "_name": "logged_features",
                                "featureset": featureset,
                                "params": params
                            }
                        }
                    ]
                }
            },
            "ext": {
                "ltr_log": {
                    "log_specs": {
                        "name": "ltr_features",
                        "named_query": "logged_features"
                    }
                }
            },
            "size": 1000
        }

        terms_query = [
            {
                "terms": {
                    "_id": ids
                }
            }
        ]

        if ids is not None:
            params["query"]["bool"]["must"] = terms_query

        resp = self.es.search(index, body=params)
        resp_msg(msg="Searching {} - {}".format(index, str(terms_query)[:20]), resp=SearchResp(resp))

        matches = []
        for hit in resp['hits']['hits']:
            hit['_source']['ltr_features'] = []

            for feature in hit['fields']['_ltrlog'][0]['ltr_features']:
                value = 0.0
                if 'value' in feature:
                    value = feature['value']

                hit['_source']['ltr_features'].append(value)

            matches.append(hit['_source'])

        return matches

    def submit_model(self, featureset, index, model_name, model_payload):
        model_ep = "{}/_model/".format(self.elastic_ep)
        create_ep = "{}/_featureset/{}/_createmodel".format(self.elastic_ep, featureset)

        resp = requests.delete('{}{}'.format(model_ep, model_name))
        print('Delete model {}: {}'.format(model_name, resp.status_code))

        resp = requests.post(create_ep, json=model_payload)
        resp_msg(msg="Created Model {}".format(model_name), resp=resp)

    def submit_ranklib_model(self, featureset, index, model_name, model_payload):
        params = {
            'model': {
                'name': model_name,
                'model': {
                    'type': 'model/ranklib',
                    'definition': model_payload
                }
            }
        }
        self.submit_model(featureset, index, model_name, params)

    def model_query(self, index, model, model_params, query):
        params = {
            "query": query,
            "rescore": {
                "window_size": 1000,
                "query": {
                    "rescore_query": {
                        "sltr": {
                            "params": model_params,
                            "model": model
                        }
                    }
                }
            },
            "size": 1000
        }

        resp = self.es.search(index, body=params)
        resp_msg(msg="Searching {} - {}".format(index, str(query)[:20]), resp=SearchResp(resp))

        # Transform to consistent format between ES/Solr
        matches = []
        for hit in resp['hits']['hits']:
            matches.append(hit['_source'])

        return matches

    def query(self, index, query):
        resp = self.es.search(index, body=query)
        resp_msg(msg="Searching {} - {}".format(index, str(query)[:20]), resp=SearchResp(resp))

        # Transform to consistent format between ES/Solr
        matches = []
        for hit in resp['hits']['hits']:
            hit['_source']['_score'] = hit['_score']
            matches.append(hit['_source'])

        return matches

    def feature_set(self, index, name):
        resp = requests.get('{}/_featureset/{}'.format(self.elastic_ep,
                                                      name))

        jsonResp = resp.json()
        if not jsonResp['found']:
            raise RuntimeError("Unable to find {}".format(name))

        resp_msg(msg="Fetched FeatureSet {}".format(name), resp=resp)

        rawFeatureSet = jsonResp['_source']['featureset']['features']

        mapping = []
        for feature in rawFeatureSet:
            mapping.append({'name': feature['name']})

        return mapping, rawFeatureSet

    def get_doc(self, doc_id, index):
        resp = self.es.get(index=index, id=doc_id)
        #resp_msg(msg="Fetched Doc".format(docId), resp=ElasticResp(resp), throw=False)
        return resp['_source']
"""