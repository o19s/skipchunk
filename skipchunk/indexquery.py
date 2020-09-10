import json
import pysolr

from os import listdir
from os.path import isfile, join

from . import solr

## -------------------------------------------
## Indexing!

def indexableDocuments(path):
    #This is probably inefficient and can be improved with a bulk process or threads
    for f in listdir(path):
        filename = join(path, f) 
        if isfile(filename) and '.json' in filename:
            with open(filename) as doc:
                yield json.load(doc)

##==========================================================
# MAIN API ENTRY POINT!  USE THIS!

class IndexQuery():

    ## -------------------------------------------
    # Accepts a skipchunk object to index the required data in Solr
    def index(self,skipchunk,timeout=10000):

        isCore = solr.indexExists(self.host,skipchunk.indexname)
        if not isCore:
            isCore = solr.indexCreate(self.host,skipchunk.indexname,skipchunk.solr_index_data)

        if isCore:
            indexer = pysolr.Solr(self.solr_uri, timeout=timeout)
            indexer.add(list(indexableDocuments(skipchunk.document_data)),commit=True)

    def cores(self):
        cores = solr.indexList(self.host)
        indexes = [name for name in cores if '-index' in name]
        return indexes

    def changeCore(self,name):
        if solr.indexExists(self.host,name):
            self.name = name + '-index'
            self.solr_uri = self.host + self.name
            self.select_handler = pysolr.Solr(self.solr_uri)
            return True
        return False

    ## -------------------------------------------
    # Pretty-prints a graph walk of all suggested concepts and their verbs given a starting term prefix

    def search(self,query):
        return solr.passthrough(self.solr_uri,'&'+query)

    ## -------------------------------------------
    # host:: the url of the solr server
    # name:: the name of the solr core
    def __init__(self,host,name):
        self.host = host
        self.name = name + '-index'
        self.solr_uri = self.host + self.name
        self.select_handler = pysolr.Solr(self.solr_uri)


##==========================================================
# Command line explorer!

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
