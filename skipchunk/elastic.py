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
def resp_msg(msg, resp, throw=True):
    print('{} [Status: {}]'.format(msg, resp.status_code))
    if resp.status_code >= 400:
        print(resp.text)
        if throw:
            raise RuntimeError(resp.text)


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
    def indexes(self) -> list:
        #List the existing indexes of the given kind

        indexes = []

        host = self.host
        uri = host + "_cat/indices?format=json"

        try:
            r = requests.get(uri)
            if r.status_code == 200:
                #Say cheese
                indexes = r.json()
                indexes = [i.index.replace('-' + self.kind,'') for i in indexes if '-'+self.kind in i.index]

            else:
                print('ELASTIC ERROR! Cores could not be listed! Have a nice day.')
                print(json.dumps(r.json(),indent=2))

        except:
            message = 'NETWORK ERROR! Could not connect to Elastic server on',uri,' ... Have a nice day.'
            raise ValueError(message)  

        return indexes      


    def indexExists(self,name: str) -> bool:
        #Returns true if the index exists on the host
        host = self.host
        uri = host + name
        r = requests.get(uri)
        if r.status_code == 200:
            data = r.json()
            if name in data.keys():
                return True
        return False

    def indexCreate(self,timeout=10000) -> bool:
        #Creates a new index with a specified configuration

        #Set this to true only when core is created
        success = False

        host = self.host
        name = self.name
        path = self.root

        if not self.indexExists(name):
            try:

                if os.path.isdir(self.elastic_home):
                    shutil.rmtree(self.elastic_home)

                #Create the directories to hold the Elastic conf and data
                module_dir = os.path.dirname(os.path.abspath(__file__))
                pathlen = module_dir.rfind('/')+1
                graph_source = module_dir[0:pathlen] + '/elastic_home/configsets/skipchunk-'+self.kind+'-configset'
                shutil.copytree(graph_source,self.elastic_home)

                cfg_json_path = self.elastic_home + '/skipchunk-'+self.kind+'-schema.json'

                #Create the index in Elastic
                with open(cfg_json_path) as src:
                    settings = json.load(src)
                    res = self.es.indices.create(self.name, body=settings)
                    r = ElasticResp(res)
                    if r.status_code == 200:
                        success = True
                        #Say cheese
                        print('Index',name,'created!')
                    else:
                        print('ELASTIC ERROR! Index',name,'could not be created! Have a nice day.')
                        print(json.dumps(r.json(),indent=2))

            except:
                message = 'NETWORK ERROR! Could not connect to Elasticsearch server on',host,' ... Have a nice day.'
                raise ValueError(message)

        return success
        
    def indexDelete(self):
        resp = self.es.indices.delete(index=self.name, ignore=[400, 404])
        resp_msg(msg="Deleted index {}".format(self.name), resp=ElasticResp(resp), throw=False)


    ## -------------------------------------------
    ## Content Update
    def index(self, documents, timeout=10000) -> str:
        #Accepts a skipchunk object to index the required data

        def bulkDocs(doc_src,name):
            for doc in doc_src:
                addCmd = {"_index": name,
                          "_id": doc['id'],
                          "_source": doc}
                yield addCmd

        isIndex = self.indexExists(self.name)
        if not isIndex:
            isIndex = self.indexCreate()

        if isIndex:
            res = elasticsearch.helpers.bulk(self.es, bulkDocs(documents,self.name), chunk_size=100)
            self.es.indices.refresh(index=self.name)
            r = BulkResp(res)
            if r.status_code<400:
                return True

        return False
    ## -------------------------------------------
    ## Querying
    def search(self,querystring, handler: str) -> str:
        #Searches the engine for the query
        pass

    ## -------------------------------------------
    ## Graphing

    def parseAggregate(self,field:str,res:dict) -> dict:
        #parses an aggregate resultset normalizing against a generic interface
        facets = [{"label":f["key"],"count":f["doc_count"]} for f in res["aggregations"][field]["buckets"]]
        return facets

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
        query = {
            "size":0,
            "query": {
                "match_phrase_prefix": { 
                    "concept_suggest": prefix 
                }
            },
            "aggs": {
                "preflabel": {
                    "terms": { 
                        "field": "preflabel"
                    }
                }
            }
        }

        res = es.search(index=self.name, body=query)
        return parseAggregate(res)

    def suggestPredicates(self,prefix:str,build=False) -> list:
        # Suggests a list of predicates given a prefix
        query = {
            "size":0,
            "query": {
                "match_phrase_prefix": { 
                    "predicate_suggest": prefix
                }
            },
            "aggs": {
                "preflabel": {
                    "terms": { 
                        "field": "preflabel"
                    }
                }
            }
        }

        res = es.search(index=self.name, body=query)
        return parseAggregate(res)

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

        self.es = Elasticsearch(self.host)

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