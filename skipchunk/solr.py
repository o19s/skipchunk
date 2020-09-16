import os
import json
import pysolr
import requests
import datetime
import jsonpickle
import shutil
import urllib

from .interfaces import SearchEngineInterface

def pretty(obj):
    print(jsonpickle.encode(obj,indent=2))

## -------------------------------------------
## Java-Friendly datetime string format

def timestamp():
    return datetime.datetime.now().isoformat() + 'Z'

## -------------------------------------------
## Pass-through query!
## Just take the query as provided, run it against solr, and return the raw response

def passthrough(uri):
    req = requests.get(uri)
    return req.text,req.status_code

## -------------------------------------------
## MAIN CLASS ENTRY POINT
## 

class Solr(SearchEngineInterface):

    ## -------------------------------------------
    ## Index Admin
    def indexes(self,kind=None) -> list:        
        #List the existing indexes of the given kind

        cores = []

        host = self.host

        try:            
            #Lookup all the cores:
            uri = host + 'admin/cores?action=STATUS'

            r = requests.get(uri)
            if r.status_code == 200:
                #Say cheese
                cores = list(r.json()['status'].keys())

            else:
                print('SOLR ERROR! Cores could not be listed! Have a nice day.')
                print(json.dumps(r.json(),indent=2))

        except:
            message = 'NETWORK ERROR! Could not connect to Solr server on',host,' ... Have a nice day.'
            raise ValueError(message)
        
        return cores

    def indexExists(self,name: str) -> bool:
        #Returns true if the index exists on the host
        host = self.host

        uri = host + 'admin/cores?action=STATUS&core=' + name

        r = requests.get(uri)
        if r.status_code == 200:
            data = r.json()
            if name in data['status'].keys():
                if "name" in data['status'][name].keys():
                    if data['status'][name]["name"]==name:
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

                if not os.path.isdir(self.solr_home):
                    #Create the directories to hold the Solr conf and data
                    module_dir = os.path.dirname(os.path.abspath(__file__))
                    pathlen = module_dir.rfind('/')+1
                    graph_source = module_dir[0:pathlen] + '/solr_home/configsets/skipchunk-'+self.kind+'-configset'
                    shutil.copytree(graph_source,self.solr_home)

                #Create the core in solr
                uri = host + 'admin/cores?action=CREATE&name='+name+'&instanceDir='+self.solr_home+'/conf&config=solrconfig.xml&dataDir='+self.solr_home+'/data'
                r = requests.get(uri)
                if r.status_code == 200:
                    success = True
                    #Say cheese
                    print('Core',name,'created!')
                else:
                    print('SOLR ERROR! Core',name,'could not be created! Have a nice day.')
                    print(json.dumps(r.json(),indent=2))


            except:
                message = 'NETWORK ERROR! Could not connect to Solr server on',host,' ... Have a nice day.'
                raise ValueError(message)

        return success

    ## -------------------------------------------
    ## Content Update
    def index(self, documents, timeout=10000) -> bool:
        #Accepts documents to index the required data
        isCore = self.indexExists(self.name)
        if not isCore:
            isCore = self.indexCreate()

        if isCore:
            indexer = pysolr.Solr(self.solr_uri, timeout=timeout)
            indexer.add(documents,commit=True)

        return True

    ## -------------------------------------------
    ## Querying

    def search(self,querystring, handler: str) -> str:
        #Searches the engine for the query
        if self.enrich_query:
            querystring = self.enrich_query(querystring)

        params = []
        for t in querystring.items():
            params.append(t[0]+'='+urllib.parse.quote(t[1]))
        qs = '&'.join(params)

        uri = self.solr_uri + '/' + handler + '?' + qs
        results,status = passthrough(uri)
        return results,status

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
        return tree

    def __init__(self,host,name,kind,path):
        self.host = host
        self.name = name + '-' + kind
        self.kind = kind
        self.path = os.path.abspath(path)
        self.solr_uri = self.host + self.name

        self.root = os.path.join(self.path, name)
        self.solr_home = os.path.join(self.root, 'solr_'+self.kind)
        self.document_data = os.path.join(self.root, 'documents')
