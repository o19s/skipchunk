# -*- coding: utf-8 -*-

"""Example for `skipchunk` package."""
import json
from skipchunk import sq
from skipchunk import skipchunk as sc

if __name__ == "__main__":

    LOAD=False
    name = 'osc-blog'
    host = 'http://localhost:8983/solr/'
    source = 'blog-posts.json'

    s = sc.Skipchunk(name,
        spacy_model='en_core_web_lg',
        minconceptlength=1,
        maxconceptlength=3,
        minpredicatelength=1,
        maxpredicatelength=3,
        minlabels=1)

    q = sq.SkipchunkQuery(host,name)

    if LOAD:
        print(sq.timestamp()," | Loading Pickle")
        s.load()
    else:
        print(sq.timestamp()," | Loading Tuples")
        tuples = s.tuplize(filename=source,fields=['title','content'])
        print(sq.timestamp()," | Enriching")
        s.enrich(tuples)
        print(sq.timestamp()," | Pickling")
        s.save()

    print(sq.timestamp()," | Indexing")
    q.index(s)
    print(sq.timestamp()," | !!!~~~~~DONE~~~~~!!!")