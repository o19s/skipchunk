import os
import json
import pysolr
import requests
import datetime
import jsonpickle
import shutil
import urllib

from .interfaces import SearchEngineInterface
from .utilities import configPath

import datetime

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

def cleanTerm(term):
    return term.replace('/','\\/').replace('"','')


## -------------------------------------------
## Debug Utils

def printAggregate(agg):
    if agg:
        for f in agg:
            print(f["label"],f["count"])

def printSuggest(sugg):
    if sugg:
        for f in sugg:
            print(f["term"],f["weight"])

def pretty(obj):
    print(jsonpickle.encode(obj,indent=2))

## -------------------------------------------
## Facets/Aggregations/Suggestions

def aggregateQuery(field,mincount=1,limit=100):
    return {
        "facet.field":field,
        "facet.limit":limit,
        "facet.mincount":mincount,
        "facet":"on"
    }

def parseAggregate(field,res):
    facets = None
    if (res.facets) and ("facet_fields" in res.facets.keys()) and (field in res.facets["facet_fields"].keys()):
        labels = res.facets["facet_fields"][field]
        facets = []
        for i in range(len(labels)//2):
            facets.append({"label":labels[i*2],"count":labels[i*2+1]})

    return facets

def suggest(prefix,dictionary="conceptLabelSuggester",count=25,build=False):
    s = {
        "suggest":"true",
        "suggest.q":prefix,
        "suggest.count":count,
        "suggest.dictionary":dictionary
    }
    if build:
        s["suggest.build"] = "true"

    return s

def configPath(target_dir):
    module_dir = os.path.dirname(os.path.abspath('/Users/max/o19s/skipchunk/'))
    source_dir = module_dir[0:module_dir.rfind('/')]
    graph_source = os.path.join(source_dir,target_dir)
    return graph_source

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

        #Lookup all the cores:
        uri = host + 'admin/cores?action=STATUS'

        try:            

            r = requests.get(uri)
            if r.status_code == 200:
                #Say cheese
                cores = list(r.json()['status'].keys())
                cores = [c.replace(self.postfix,'') for c in cores if self.postfix in c]

            else:
                print('SOLR ERROR! Cores could not be listed! Have a nice day.')
                print(json.dumps(r.json(),indent=2))

        except:
            message = 'NETWORK ERROR! Could not connect to Solr server on',uri,' ... Have a nice day.'
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
                    graph_source = configPath('solr_home/configsets/skipchunk-'+self.kind+'-configset')
                    print(graph_source)
                    shutil.copytree(graph_source,self.solr_home)

            except:
                message = 'DISK ERROR! Could not find the schema at ' + graph_source
                raise ValueError(message)            

            try:

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
                uri = host + 'admin/cores?action=CREATE'
                message = 'NETWORK ERROR! Could not connect to Solr server on',uri,' ... Have a nice day.'
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

            #documents is a generator so we convert it to a list first
            indexer.add(list(documents),commit=True)

            return True

        return False

    ## -------------------------------------------
    ## Querying

    def search(self,querystring, handler: str) -> str:
        #Searches the engine for the query
        enriched = None
        if self.enrich_query:
            enriched = self.enrich_query(querystring)

        params = []
        for t in querystring.items():
            if t[0] == "q" and enriched:
                params.append('q='+urllib.parse.quote(enriched))
            else:
                params.append(t[0]+'='+urllib.parse.quote(t[1]))
        qs = '&'.join(params)

        uri = self.solr_uri + '/' + handler + '?' + qs
        results,status = passthrough(uri)
        return json.loads(results),status

    ## -------------------------------------------
    ## Graphing

    def conceptVerbConcepts(self,concept:str,verb:str,mincount=1,limit=100) -> list:
        # Accepts a verb to find the concepts appearing in the same context
        subject = cleanTerm(concept)
        verb = cleanTerm(verb)
        objects = []
        subjects = []

        # Get all the docid and sentenceid pairs that contain both the concept AND verb
        #    http://localhost:8983/solr/osc-blog/select?fl=docid%2Csentenceid&fq=subjectof%3A%22be%22%20OR%20objectof%3A%22be%22&q=label%3A%22open%20source%22&rows=1000
        q="*"
        fl="sentenceid"
        fq=["(subjectof:\""+verb+"\" OR objectof:\""+verb+"\")","preflabel:\""+subject+"\""]
        rows=10000
        res = self.select_handler.search(q=q,fq=fq,fl=fl,rows=rows)

        if len(res.docs)>0:

            # Get all the other concepts that exist in those docid and sentenceid pairs
            #   http://localhost:8983/solr/osc-blog/select?fl=*&fq=-preflabel%3A%22open%20source%22&fq=sentenceid%3A17%20AND%20docid%3Aafee4d71ccb3e19d36ee2cfddd6da618&q=contenttype%3Aconcept&rows=100
            sentences = []
            for doc in res.docs:
                sentences.append("sentenceid:"+doc["sentenceid"])
            sentenceids = " OR ".join(sentences)

            q="*"
            fq=[
                "-preflabel:\""+subject+"\"",
                "contenttype:concept",
                "(" + sentenceids + ")"
            ]
            field = "preflabel"

            facet = aggregateQuery(field,mincount,limit)
            res   = self.select_handler.search(q=q,fq=fq,rows=rows,**facet)
            objects = parseAggregate(field,res)
        
        return objects


    def conceptsNearVerb(self,verb:str,mincount=1,limit=100) -> list:
        # Accepts a verb to find the concepts appearing in the same context
        verb = cleanTerm(verb)

        field = "preflabel"
        q = "*:*"
        fq = "objectof:"+verb+" OR subjectof:"+verb

        facet = aggregateQuery(field,mincount,limit)
        res = self.select_handler.search(q=q,fq=fq,rows=0,**facet)
        aggregate = parseAggregate(field,res)

        return aggregate

    def verbsNearConcept(self,concept:str,mincount=1,limit=100) -> list:
        # Accepts a concept to find the verbs appearing in the same context
        concept = cleanTerm(concept)

        field = "subjectof"
        q = concept
        facet = aggregateQuery(field,mincount,limit)
        res = self.select_handler.search(q=q,rows=0,**facet)
        subjectofs = parseAggregate(field,res)

        field = "objectof"
        q = concept
        facet = aggregateQuery(field,mincount,limit)
        res = self.select_handler.search(q=q,rows=0,**facet)
        objectofs = parseAggregate(field,res)

        return subjectofs+objectofs

    def suggestConcepts(self,prefix:str,build=False) -> list:
        # Suggests a list of concepts given a prefix
        dictionary="conceptLabelSuggester"
        query = suggest(prefix,dictionary=dictionary,count=5,build=build)
        res = self.suggest_handler.search(q=prefix,**query)
        return res.raw_response["suggest"][dictionary][prefix]["suggestions"]

    def suggestPredicates(self,prefix:str,build=False) -> list:
        # Suggests a list of predicates given a prefix
        objectofSuggestions = []
        subjectofSuggestions = []

        dictionary1="objectofLabelSuggester"
        query1 = suggest(prefix,dictionary=dictionary1,count=5,build=build)
        res1 = self.suggest_handler.search(q=prefix,**query1)
        if dictionary1 in res1.raw_response["suggest"]:
            objectofSuggestions = res1.raw_response["suggest"][dictionary1][prefix]["suggestions"]

        dictionary2="subjectofLabelSuggester"
        query2 = suggest(prefix,dictionary=dictionary2,count=5,build=build)
        res2 = self.suggest_handler.search(q=prefix,**query2)
        if dictionary2 in res2.raw_response["suggest"]:
            subjectofSuggestions = res2.raw_response["suggest"][dictionary2][prefix]["suggestions"]

        return objectofSuggestions

    def summarize(self,mincount=1,limit=100) -> list:
        # Summarizes a core
        q  = "*"
        fq = "contenttype:concept"
        field = "preflabel"

        facet = aggregateQuery(field,mincount,limit)
        res = self.select_handler.search(q=q,fq=fq,rows=0,**facet)
        concepts = parseAggregate(field,res)

        q2  = "*"
        fq2 = "contenttype:predicate"
        field2 = "preflabel"

        facet2 = aggregateQuery(field2,mincount,limit)
        res2 = self.select_handler.search(q=q2,fq=fq2,rows=0,**facet2)
        predicates = parseAggregate(field2,res2)

        return concepts,predicates

    def graph(self,subject:str,objects=5,branches=10) -> list:
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

        tree = []

        if contenttype == "concept":
            if not quiet:
                print("\n=================FINDING '"+term+"' ==================")
            for s in self.suggestConcepts(term,build=build):
                verbs = self.verbsNearConcept(s["term"])[0:branches]
                c = s["term"]
                branch = {
                    "label":c,
                    "weight":s["weight"],
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
                    cvc = self.conceptVerbConcepts(c,v,limit=5)
                    for o in cvc:
                        predicate["relationships"].append({
                            "label":o["label"],
                            "weight":o["count"],
                            "labeltype":"object",
                            "relationships":[]
                        })
                    branch["relationships"].append(predicate)

                tree.append(branch)

                if not quiet:
                    lst = ', '.join([a["label"]+"("+str(a["count"])+")" for a in verbs])
                    print("")
                    print(s["term"] + " (" + str(s["weight"]) + ")")
                    print('\t',lst)
                    print("")
                    print('----------------------------------------------------')
        
        elif contenttype == "predicate":
            if not quiet:
                print("\n=================FINDING '"+term+"' ==================")
            for s in self.suggestPredicates(term,build=build):
                concepts = self.conceptsNearVerb(s["term"])[0:branches]
                tree[s["term"]] = concepts
                if not quiet:
                    lst = ', '.join([a["label"]+"("+str(a["count"])+")" for a in verbs])
                    print("")
                    print(s["term"] + " (" + str(s["weight"]) + ")")
                    print('\t',lst)
                    print("")
                    print('----------------------------------------------------')

        return tree

    def __init__(self,host,name,kind,path,postfix,enrich_query=None):
        self.host = host
        self.name = name + postfix
        self.kind = kind
        self.path = os.path.abspath(path)
        self.postfix = postfix
        self.solr_uri = self.host + self.name

        self.root = os.path.join(self.path, name)
        self.solr_home = os.path.join(self.root, 'solr_'+self.kind)
        self.document_data = os.path.join(self.root, 'documents')

        self.select_handler = pysolr.Solr(self.solr_uri, search_handler='/select')

        self.enrich_query = enrich_query

        if kind == "graph":
            self.suggest_handler = pysolr.Solr(self.solr_uri, search_handler='/suggest')

