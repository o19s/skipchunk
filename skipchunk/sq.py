import json
import pysolr
import requests
import os
import shutil
import datetime
from datetime import date as dt

## -------------------------------------------

def timestamp():
    return datetime.datetime.now().isoformat() + 'Z'

## -------------------------------------------
## Indexing!

def coreExists(host,name):
    uri = host + 'admin/cores?action=STATUS&core=' + name
    r = requests.get(uri)
    if r.status_code == 200:
        data = r.json()
        if name in data['status'].keys():
            if "name" in data['status'][name].keys():
                if data['status'][name]["name"]==name:
                    return True
    return False


def coreCreate(host,name,path,timeout=10000):

    #Set this to true only when core is created
    success = False

    if not coreExists(host,name):
        try:            
            #Create the core in solr
            uri = host + 'admin/cores?action=CREATE&name='+name+'&instanceDir='+path+'/conf&config=solrconfig.xml&dataDir='+path+'/data'
            r = requests.get(uri)
            if r.status_code == 200:
                success = True
                #Say cheese
                print('Core',name,'created!')
            else:
                print('SOLR ERROR! Core',name,'could not be created! Have a nice day.')
                print(json.dumps(r.json(),indent=2))

        except:
            print('NETWORK ERROR! Could not connect to Solr server on',host,' ... Have a nice day.')

    return success

def indexableGroups(groups,contenttype='concept'):
    """ Generates concept records for Solr, similar to how ES Bulk indexing
        uses a generator to generate bulk index/update actions """
    createtime = timestamp()
    for group in groups:
        key = group.key
        for label in group.labels:
            labelid = group.key + '_' + str(label.docid) + '_' + str(label.sentenceid)
            print("Indexing %s" % labelid)

            record = {
                'id' : labelid,
                'key' : key,
                'idiom' : label.idiom,
                'label' : label.label,
                'length' : label.length,
                'start' : label.start,
                'end' : label.end,
                'docid' : label.docid,
                'sentenceid' : label.sentenceid,
                'objectof' : label.objectOf,
                'subjectof' : label.subjectOf,
                'contenttype' : contenttype,
                'createtime': createtime,
                #Group-level values
                'preflabel' : group.preflabel,
                'prefcount' : group.prefcount,
                'total' : group.total
            }

            #For separate concept/predict behavior (such as autosuggest)
            if contenttype == 'concept':
                record['conceptlabel'] = label.label
            else:
                record['predicatelabel'] = label.label

            ##Generator for the record
            yield record

## -------------------------------------------

def indexableLabels(labels,contenttype='concept'):
    """ Generates labels for indexing, similar to how ES Bulk indexing
        uses a generator to generate bulk index/update actions """

    createtime = timestamp()
    for key in labels.keys():
        for label in labels[key]:
            labelid = key + '_' + str(label.docid) + '_' + str(label.sentenceid)

            print("Indexing %s" % labelid)

            record = {
                'id' : labelid,
                'key' : key,
                'idiom' : label.idiom,
                'label' : label.label,
                'length' : label.length,
                'start' : label.start,
                'end' : label.end,
                'docid' : label.docid,
                'sentenceid' : label.sentenceid,
                'objectof' : label.objectOf,
                'subjectof' : label.subjectOf,
                'contentType' : contenttype,
                'createtime': creattime
            }

            if contenttype == 'concept':
                record['conceptlabel'] = label.label
            else:
                record['predicatelabel'] = label.label

            ##Generator for the record
            yield record

## -------------------------------------------
## Querying shortcuts

def printAggregate(agg):
    if agg:
        for f in agg:
            print(f["label"],f["count"])

def printSuggest(sugg):
    if sugg:
        for f in sugg:
            print(f["term"],f["weight"])

def cleanTerm(term):
    return term.replace('/','\\/').replace('"','')

## -------------------------------------------
## Facets

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

## -------------------------------------------
## Suggestions

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

##==========================================================
# MAIN API ENTRY POINT!  USE THIS!

class SkipchunkQuery():

    ## -------------------------------------------
    # Accepts a skipchunk object to index the required data in Solr
    def index(self,skipchunk,timeout=10000):

        isCore = coreExists(self.host,skipchunk.name)
        if not isCore:
            isCore = coreCreate(self.host,skipchunk.name,skipchunk.solr_data)

        if isCore:
            indexer = pysolr.Solr(self.solr_uri, timeout=timeout)
            indexer.add(list(indexableGroups(skipchunk.predicategroups,contenttype="predicate")),commit=True)
            indexer.add(list(indexableGroups(skipchunk.conceptgroups,contenttype="concept")),commit=True)

    ## -------------------------------------------
    # Uses a streaming expression to fill in missing prefLabels after indexing
    def makePrefLabels():    
        # TODO: Write this
        return 0

    ## -------------------------------------------
    # Accepts a verb to find the concepts appearing in the same context

    def conceptsNearVerb(self,verb,mincount=1,limit=100):
        
        verb = cleanTerm(verb)

        field = "preflabel"
        q = "*:*"
        fq = "objectof:"+verb+" OR subjectof:"+verb

        facet = aggregateQuery(field,mincount,limit)
        res = self.select_handler.search(q=q,fq=fq,rows=0,**facet)
        aggregate = parseAggregate(field,res)

        return aggregate

    ## -------------------------------------------
    # Accepts a concept to find the verbs appearing in the same context

    def verbsNearConcept(self,concept,mincount=1,limit=100):

        concept = cleanTerm(concept)

        field = "objectof"
        q = concept

        facet = aggregateQuery(field,mincount,limit)
        res = self.select_handler.search(q=q,rows=0,**facet)
        aggregate = parseAggregate(field,res)

        return aggregate

    ## -------------------------------------------
    # Suggests a list of concepts given a prefix

    def suggestConcepts(self,prefix,build=False):
        dictionary="conceptLabelSuggester"
        query = suggest(prefix,dictionary=dictionary,count=5,build=build)
        res = self.suggest_handler.search(q=prefix,**query)
        return res.raw_response["suggest"][dictionary][prefix]["suggestions"]

    ## -------------------------------------------
    # Suggests a list of predicates given a prefix

    def suggestPredicates(self,prefix,build=False):

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

    ## -------------------------------------------
    # Pretty-prints a graph walk of all suggested concepts and their verbs given a starting term prefix

    def explore(self,term,contenttype="concept",build=False):

        if contenttype == "concept":
            print("\n=================FINDING '"+term+"' ==================")
            for s in self.suggestConcepts(term,build=build):
                agg = self.verbsNearConcept(s["term"])
                lst = ', '.join([a["label"]+"("+str(a["count"])+")" for a in agg][0:10])
                print("")
                print(s["term"] + " (" + str(s["weight"]) + ")")
                print('\t',lst)
                print("")
                print('----------------------------------------------------')
        
        elif contenttype == "predicate":
            print("\n=================FINDING '"+term+"' ==================")
            for s in self.suggestPredicates(term,build=build):
                agg = self.conceptsNearVerb(s["term"])
                lst = ', '.join([a["label"]+"("+str(a["count"])+")" for a in agg][0:10])
                print("")
                print(s["term"] + " (" + str(s["weight"]) + ")")
                print('\t',lst)
                print("")
                print('----------------------------------------------------')

    ## -------------------------------------------
    # host:: the url of the solr server
    # name:: the name of the solr core
    def __init__(self,host,name):
        self.host = host
        self.name = name
        self.solr_uri = host + name
        self.select_handler = pysolr.Solr(self.solr_uri)
        self.suggest_handler = pysolr.Solr(self.solr_uri, search_handler='/suggest')


##==========================================================
# Command line explorer!

if __name__ == "__main__":
    import sys
    import jsonpickle

    def pretty(obj):
        print(jsonpickle.encode(obj,indent=2))

    i=1
    if sys.argv[0]=='python':
        i=2

    if len(sys.argv)<i+3:
        print('python sq.py <solr_core_name> <concept|predicate> <term>')

    core = sys.argv[i]
    kind = sys.argv[i+1]
    term = sys.argv[i+2]

    if coreExists('http://localhost:8983/solr/',core):
        sq = SkipchunkQuery('http://localhost:8983/solr/',core)
        sq.explore(term,contenttype=kind,build=False)
    else:
        print('Core "',core,'" does not exists on localhost')
