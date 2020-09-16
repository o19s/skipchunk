import json
import pysolr
from . import solr

## -------------------------------------------
## Indexing!

def indexableGroups(groups,contenttype='concept'):
    """ Generates concept records for Solr, similar to how ES Bulk indexing
        uses a generator to generate bulk index/update actions """
    createtime = solr.timestamp()
    for group in groups:
        key = group.key
        for label in group.labels:
            snippetid = str(label.docid) + '_' + str(label.sentenceid)
            labelid = group.key + '_' + snippetid
            #print("Indexing %s" % labelid)

            record = {
                'id' : labelid,
                'key' : key,
                'idiom' : label.idiom,
                'label' : label.label,
                'length' : label.length,
                'start' : label.start,
                'end' : label.end,
                'docid' : label.docid,
                'sentenceid' : snippetid,
                'sentencenum_s' : label.sentenceid,
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

    createtime = solr.timestamp()
    for key in labels.keys():
        for label in labels[key]:
            labelid = key + '_' + str(label.docid) + '_' + str(label.sentenceid)

            #print("Indexing %s" % labelid)

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

class GraphQuery():

    ## -------------------------------------------
    # Accepts a skipchunk object to index the required data in Solr

    def index(self,skipchunk,timeout=10000):
        predicatedocs = list(indexableGroups(skipchunk.predicategroups,contenttype="predicate"))
        conceptdocs = list(indexableGroups(skipchunk.conceptgroups,contenttype="concept"))
        return self.engine.index(conceptdocs+predicatedocs,timeout=timeout)

    def indexes(self):
        return self.engine.indexes(self.kind)

    """
    def index2(self,skipchunk,timeout=10000):
        isCore = solr.indexExists(self.host,skipchunk.graphname)
        if not isCore:
            isCore = solr.indexCreate(self.host,skipchunk.graphname,skipchunk.solr_graph_data)

        if isCore:
            indexer = pysolr.Solr(self.solr_uri, timeout=timeout)
            indexer.add(list(indexableGroups(skipchunk.predicategroups,contenttype="predicate")),commit=True)
            indexer.add(list(indexableGroups(skipchunk.conceptgroups,contenttype="concept")),commit=True)
    
    def cores(self):
        cores = solr.indexList(self.host)
        indexes = [name for name in cores if '-graph' in name]
        return indexes

    def changeCore(self,name):
        if solr.indexExists(self.host,name):
            self.name = name
            if '-graph' not in name:
                self.name += '-graph'        
            self.solr_uri = self.host + self.name
            self.select_handler = pysolr.Solr(self.solr_uri)
            self.suggest_handler = pysolr.Solr(self.solr_uri, search_handler='/suggest')            
            return True
        return False
    """

    ## -------------------------------------------
    # Uses a streaming expression to fill in missing prefLabels after indexing
    def makePrefLabels():    
        # TODO: Write this
        return 0

    ## -------------------------------------------
    # Accepts a verb to find the concepts appearing in the same context

    def conceptVerbConcepts(self,concept,verb,mincount=1,limit=100):
        
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
                #"(subjectof:\""+verb+"\" OR objectof:\""+verb+"\")",
                "(" + sentenceids + ")"
            ]
            field = "preflabel"

            facet = aggregateQuery(field,mincount,limit)
            res   = self.select_handler.search(q=q,fq=fq,rows=rows,**facet)
            objects = parseAggregate(field,res)
        
        return objects

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
    # Summarizes a core

    def summarize(self,mincount=1,limit=100):

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

    ## -------------------------------------------
    # Gets the subject-predicate-object graph for a subject

    def graph(self,subject,objects=5,branches=10):

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

    ## -------------------------------------------
    # Pretty-prints a graph walk of all suggested concepts and their verbs given a starting term prefix

    def explore(self,term,contenttype="concept",build=False,quiet=False,branches=10):

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

    ## -------------------------------------------
    # host:: the url of the solr server
    # name:: the name of the solr core
    def __init__(self,config):
        self.kind = "graph"
        self.host = config["host"]
        self.name = config["name"]
        self.engine_name = config["engine_name"].lower()
        self.path = config["path"]

        #Setup the search engine
        if self.engine_name in ["solr"]:
            self.engine = solr.Solr(self.host,self.name,self.kind,self.path)

        elif self.engine_name in ["elasticsearch","elastic","es"]:
            raise ValueError("Sorry! Elastic isn't ready yet")
        
        else:
            raise ValueError("Sorry! Only Solr or Elastic are currently supported")

        if '-graph' not in self.name:
            self.name += '-graph'
        self.solr_uri = self.host + self.name
        self.select_handler = pysolr.Solr(self.solr_uri)
        self.suggest_handler = pysolr.Solr(self.solr_uri, search_handler='/suggest')


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

            if solr.indexExists('http://localhost:8983/solr/',core):
                sq = GraphQuery('http://localhost:8983/solr/',core)
                #sq.explore(term,contenttype=kind,build=False)
                sq.graph(term)
            else:
                print('Core "',core,'" does not exists on localhost')
