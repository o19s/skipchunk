# -*- coding: utf-8 -*-

"""Example for `skipchunk` package."""
import json
from skipchunk.graphquery import GraphQuery
from skipchunk.indexquery import IndexQuery
from skipchunk.solr import timestamp
from skipchunk import skipchunk as sc

if __name__ == "__main__":

    LOAD   = False

    skipchunk_config = {
        "host":"http://localhost:8983/solr/",
        "name":"osc-blog",
        "path":"./skipchunk_data",
        "engine_name":"solr"
    }

    source = "blog-posts.json"
    #source = "blog-posts-one.json"

    print(timestamp()," | Initializing")

    s = sc.Skipchunk(skipchunk_config,
        spacy_model="en_core_web_lg",
        minconceptlength=1,
        maxconceptlength=3,
        minpredicatelength=1,
        maxpredicatelength=3,
        minlabels=1)

    gq = GraphQuery(skipchunk_config)
    iq = IndexQuery(skipchunk_config)

    if LOAD:
        print(timestamp()," | Loading Pickle")
        s.load()
    else:
        print(timestamp()," | Loading Tuples")
        tuples = s.tuplize(filename=source,fields=['title','content'])
        print(timestamp()," | Enriching")
        s.enrich(tuples)
        print(timestamp()," | Pickling")
        s.save()

    print(timestamp()," | Indexing Graph")
    gq.index(s)

    print(timestamp()," | Indexing Content")
    iq.index()
    
    print(timestamp()," | !!!~~~~~DONE~~~~~!!!")