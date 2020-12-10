# -*- coding: utf-8 -*-

"""Example for `skipchunk` package."""
import json
from skipchunk.graphquery import GraphQuery
from skipchunk.elastic import timestamp
from skipchunk import skipchunk as sc

if __name__ == "__main__":

    # If you set LOAD=True, this will load what you previously enriched from a pickle file
    # If you haven't saved anything to pickle yet, don't enable this
    # WARNING! This file can get very big.
    LOAD = False

    skipchunk_config_elastic = {
        "host":"http://localhost:9200/",
        "name":"osc-blog",
        "path":"./skipchunk_data",
        "engine_name":"elasticsearch"
    }

    skipchunk_config = skipchunk_config_elastic

    #source = "blog-posts.json"
    source = "blog-posts-one.json"

    print(timestamp()," | Initializing")

    s = sc.Skipchunk(skipchunk_config,
        spacy_model="en_core_web_lg",
        minconceptlength=1,
        maxconceptlength=3,
        minpredicatelength=1,
        maxpredicatelength=3,
        minlabels=1,
        cache_documents=True,
        cache_pickle=True)

    gq = GraphQuery(skipchunk_config)

    if LOAD:
        print(timestamp()," | Loading Pickle")
        s.load()

    else:
        
        # Produces a list of (text,document) tuples ready for processing by the enrichment.
        print(timestamp()," | Loading Content")
        tuples = s.tuplize(filename=source,fields=['title','content'])

        # Enriching can take a long time if you provide lots of text.  Consider batching at 10k docs at a time.
        print(timestamp()," | Enriching")
        s.enrich(tuples)

        # This will save a pickle file for later on.
        # WARNING! The files can get very big.  Be careful out there!
        print(timestamp()," | Pickling")
        s.save()


    print(timestamp()," | Indexing Graph")
    gq.delete() # In this example the graph is deleted and reindexed every time.  You probably don't want to do this in real life :)
    gq.index(s)
    
    print(timestamp()," | !!!~~~~~DONE~~~~~!!!")