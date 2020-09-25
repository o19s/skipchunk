from multidict import MultiDict
import spacy

class SearchEngineInterface:

    ## -------------------------------------------
    ## Index Admin
    def indexes(self, kind=None) -> list:
        #List the existing indexes of the given kind
        pass

    def indexExists(self,name: str) -> bool:
        #Returns true if the index exists on the host
        pass

    def indexCreate(self,timeout=10000) -> bool:
        #Creates a new index for the already initialized engine params
        pass

    def indexDelete(self,timeout=10000) -> bool:
        #Deletes the index as specified in the initialized engine params
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
