import json
import os

from . import solr
from . import elastic

## -------------------------------------------
## Indexing!

def indexableDocuments(path):
    #This is probably inefficient and can be improved with a bulk process or threads
    for f in os.listdir(path):
        filename = os.path.join(path, f) 
        if os.path.isfile(filename) and '.json' in filename:
            with open(filename) as doc:
                yield json.load(doc)

##==========================================================
# MAIN API ENTRY POINT!  USE THIS!

class IndexQuery():

    ## -------------------------------------------
    # Indexes content into the engine from the configured data directory
    def index(self,timeout=10000):
        return self.engine.index(indexableDocuments(self.engine.document_data),timeout=timeout)

    def indexDocument(self,document,timeout=10000):
        return self.engine.index([document],timeout=timeout)

    def indexGenerator(self,generator,timeout=10000):
        return self.engine.index(generator,timeout=timeout)

    def indexes(self):
        return self.engine.indexes()

    def delete(self):
        return self.engine.indexDelete()

    ## -------------------------------------------
    # Pretty-prints a graph walk of all suggested concepts and their verbs given a starting term prefix

    def search(self,querystring,handler="select"):
        return self.engine.search(querystring,handler=handler)

    ## -------------------------------------------
    # host:: the url of the search engine server
    # name:: the name of the index or collection
    def __init__(self,config,enrich_query=None):
        self.kind = "index"
        self.host = config["host"]
        self.name = config["name"]
        self.path = config["path"]
        self.postfix = ""

        self.engine_name = config["engine_name"].lower()
        
        if enrich_query:
            self.enrich_query = enrich_query.enrich
        else:
            self.enrich_query = None

        #Setup the search engine
        if self.engine_name in ["solr"]:
            self.engine_name = "solr"
            self.engine = solr.Solr(self.host,self.name,self.kind,self.path,self.postfix,enrich_query=self.enrich_query)
            
        elif self.engine_name in ["elasticsearch","elastic","es"]:
            self.engine_name = "elastic"
            self.engine = elastic.Elastic(self.host,self.name,self.kind,self.path,self.postfix,enrich_query=self.enrich_query)
        
        else:
            raise ValueError("Sorry! Only Solr or Elastic are currently supported")



##==========================================================
# Command line explorer!
"""
if __name__ == "__main__":
    import sys
    import jsonpickle

    def pretty(obj):
        print(jsonpickle.encode(obj,indent=2))

    if len(sys.argv)<3:
        print('python sq.py <solr_core_name> <concept|predicate> <term>')

    else:
        i=1
        if sys.argv[0]=='python':
            i=2

        if len(sys.argv)<i+3:
            print('python sq.py <solr_core_name> <concept|predicate> <term>')
        else:
            core = sys.argv[i]
            kind = sys.argv[i+1]
            term = sys.argv[i+2]

            if coreExists('http://localhost:8983/solr/',core):
                sq = SkipchunkQuery('http://localhost:8983/solr/',core)
                #sq.explore(term,contenttype=kind,build=False)
                sq.graph(term)
            else:
                print('Core "',core,'" does not exists on localhost')
"""