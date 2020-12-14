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
from .utilities import configPath

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
## Fix search terms for searchy searchy

def cleanTerm(term):
    return term.replace('/','\\/').replace('"','')

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
                indexes = [i["index"].replace(self.postfix,'') for i in indexes if self.postfix in i["index"]]

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

        settings = None

        if not self.indexExists(name):

            configset_ok = False

            try:
                if os.path.isdir(self.elastic_home):
                    shutil.rmtree(self.elastic_home)

                #Create the directories to hold the Elastic conf and data
                graph_source = configPath('elastic_home/configsets/skipchunk-'+self.kind+'-configset')
                shutil.copytree(graph_source,self.elastic_home)
                cfg_json_path = self.elastic_home + '/skipchunk-'+self.kind+'-schema.json'

                #Create the index in Elastic
                with open(cfg_json_path) as src:
                    settings = json.load(src)

            except:
                message = 'DISK ERROR! Could not find the schema at ' + graph_source
                raise ValueError(message)

            if settings:
                try:
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

    def parseSuggest(self,field:str,res:dict) -> dict:
        #parses an aggregate resultset normalizing against a generic interface
        facets = [{"term":f["key"],"weight":f["doc_count"]} for f in res["aggregations"][field]["buckets"]]
        return facets

    def parseAggregate(self,field:str,res:dict) -> dict:
        #parses an aggregate resultset normalizing against a generic interface
        facets = [{"label":f["key"],"count":f["doc_count"]} for f in res["aggregations"][field]["buckets"]]
        return facets

    def conceptVerbConcepts(self,concept:str,verb:str,mincount=1,limit=100) -> list:
        # Accepts a verb to find the concepts appearing in the same context
        subject = cleanTerm(concept)
        verb = cleanTerm(verb)
        objects = []
        subjects = []

        # Get all the docid and sentenceid pairs that contain both the concept AND verb

        query = {
            "size":10000,
            "_source": ["sentenceid"],
            "query": {
              "bool": {
                "must":[
                    {"bool":{
                        "should": [
                          {"match": {
                            "objectof": verb
                          }},
                          {"match": {
                            "subjectof": verb
                          }}
                        ]                    
                    }},
                    {
                      "match":{
                          "preflabel": subject
                      }
                    }
                ]
              }
            }
        }
        
        res = self.es.search(index=self.name, body=query)
        #res = ElasticResp(r)

        if res["hits"]["total"]["value"]>0:

            # Get all the other concepts that exist in those docid and sentenceid pairs
            #   http://localhost:8983/solr/osc-blog/select?fl=*&fq=-preflabel%3A%22open%20source%22&fq=sentenceid%3A17%20AND%20docid%3Aafee4d71ccb3e19d36ee2cfddd6da618&q=contenttype%3Aconcept&rows=100
            sentences = []
            shoulds = []

            for doc in res["hits"]["hits"]:
                sentenceid = doc["_source"]["sentenceid"]
                sentences.append({
                    "term": {"sentenceid":sentenceid}
                })
                shoulds.append({
                    "bool": {
                        "must": [
                            {"term": {"contenttype": "concept"}},
                            {"term": {"sentenceid": sentenceid}}
                        ],
                        "must_not": [
                            {"term": {"preflabel": subject}}
                        ]
                    }
                })

            field2 = "preflabel"

            query2 = {
                "size":0,
                "query": {
                    "bool": {
                        "should": shoulds
                    }
                },
                "aggs": {
                    "preflabel": {
                        "terms": { 
                            "field": field2
                        }
                    }
                }
            }

            res2 = self.es.search(index=self.name, body=query2)
            objects = self.parseAggregate(field2,res2)
        
        return objects

    def conceptsNearVerb(self,verb:str,mincount=1,limit=100) -> list:
        # Accepts a verb to find the concepts appearing in the same context
        verb = cleanTerm(verb)

        field = "preflabel"

        query = {
            "size":0,
            "query": {
              "bool": {
                "should": [
                  {"match": {
                    "objectof": verb
                  }},
                  {"match": {
                    "subjectof": verb
                  }}
                ]
              }
            },
            "aggs": {
                "preflabel": {
                    "terms": { 
                        "field": field
                    }
                }
            }
        }

        res = self.es.search(index=self.name, body=query)
        return parseAggregate(field,res)

    def verbsNearConcept(self,concept:str,mincount=1,limit=100) -> list:
        # Accepts a concept to find the verbs appearing in the same context
        concept = cleanTerm(concept)

        field1 = "subjectof"
        field2 = "objectof"

        query1 = {
            "size":0,
            "query": {
                "match_phrase": { 
                    "label": concept
                }
            },
            "aggs": {
                "subjectof": {
                    "terms": { 
                        "field": field1
                    }
                }
            }
        }

        query2 = {
            "size":0,
            "query": {
                "match_phrase": { 
                    "label": concept
                }
            },
            "aggs": {
                "objectof": {
                    "terms": { 
                        "field": field2
                    }
                }
            }
        }

        res1 = self.es.search(index=self.name, body=query1)
        subjectofs = self.parseAggregate(field1,res1)

        res2 = self.es.search(index=self.name, body=query2)
        objectofs = self.parseAggregate(field2,res2)

        return subjectofs+objectofs

    def suggestConcepts(self,prefix:str,build=False) -> list:
        # Suggests a list of concepts given a prefix

        field = "preflabel"

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

        res = self.es.search(index=self.name, body=query)
        return self.parseSuggest(field,res)

    def suggestPredicates(self,prefix:str,build=False) -> list:
        # Suggests a list of predicates given a prefix
        
        field = "preflabel"

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

        res = self.es.search(index=self.name, body=query)
        return self.parseSuggest(field,res)

    def summarize(self,mincount=1,limit=100) -> list:
        # Summarizes a core

        field = "preflabel"

        q1 = {
            "size":0,
            "query": {
                "match": { 
                    "contenttype":"concept"
                }
            },
            "aggs": {
                "preflabel": {
                    "terms": {
                        "size":limit,
                        "field": "preflabel"
                    }
                }
            }
        }

        q2 = {
            "size":0,
            "query": {
                "match": { 
                    "contenttype":"predicate"
                }
            },
            "aggs": {
                "preflabel": {
                    "terms": {
                        "size":limit, 
                        "field": "preflabel"
                    }
                }
            }
        }

        res1 = self.es.search(index=self.name, body=q1)
        concepts = self.parseAggregate(field,res1)

        res2 = self.es.search(index=self.name, body=q2)
        predicates = self.parseAggregate(field,res2)

        return concepts,predicates


    def graph(self,subject:str,objects=5,branches=10) -> list:
        # Gets the subject-predicate-object graph for a subject

        # Gets the subject-predicate-object graph for a subject
        tree = []

        verbs = self.verbsNearConcept(subject)[0:branches]
        branch = {
            "label":subject,
            "labeltype":"subject",
            "relationships":[]
        }
        for verb in verbs:
            v = verb["label"]
            predicate = {
                "label":v,
                "weight":verb["count"],
                "labeltype":"predicate",
                "relationships":[]
            }
            cvc = self.conceptVerbConcepts(subject,v,limit=objects)
            for o in cvc:
                predicate["relationships"].append({
                    "label":o["label"],
                    "weight":o["count"],
                    "labeltype":"object",
                    "relationships":[]
                })
            branch["relationships"].append(predicate)

        tree.append(branch)

        return tree

    def explore(self,term,contenttype="concept",build=False,quiet=False,branches=10) -> list:
        # Pretty-prints a graph walk of all suggested concepts and their verbs given a starting term prefix
        return []

    def __init__(self,host,name,kind,path,postfix,enrich_query=None):
        self.host = host
        self.name = name + postfix
        self.kind = kind
        self.path = os.path.abspath(path)
        self.postfix = postfix

        self.root = os.path.join(self.path, name)
        self.elastic_home = os.path.join(self.root, 'elastic_'+self.kind)
        self.document_data = os.path.join(self.root, 'documents')

        self.elastic_uri = self.host + self.name

        self.enrich_query = enrich_query

        self.es = Elasticsearch(self.host)