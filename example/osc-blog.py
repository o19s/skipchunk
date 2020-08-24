# -*- coding: utf-8 -*-

"""Example for `skipchunk` package."""
import json
import sq
from skipchunk import skipchunk as sc

## -----------------------------

def getDocsToEnrich(filename):
    spacer = '.  '
    tuples = []
    with open(filename) as fd:
        data = json.load(fd)
    for post in data:
        text = post['title'] + spacer + spacer.join(post['content'])
        tuples.append((text,post))
    return tuples

## -----------------------------

if __name__ == "__main__":

    LOAD=False
    name = 'osc-blog'
    host = 'http://localhost:8983/solr/'
    source = 'blog-posts.json'

    s = sc.Skipchunk(name,spacy_model='en_core_web_lg',minconceptlength=2,maxconceptlength=3,minpredicatelength=1,maxpredicatelength=3,minlabels=3)

    q = sq.SkipchunkQuery(host,name)

    if LOAD:
        print(sq.timestamp()," | Loading Pickle")
        s.load()
    else:
        print(sq.timestamp()," | Loading Tuples")
        tuples = getDocsToEnrich(source)
        print(sq.timestamp()," | Enriching")
        s.enrich(tuples)
        print(sq.timestamp()," | Pickling")
        s.save()

    print(sq.timestamp()," | Indexing")
    q.index(s)
    print(sq.timestamp()," | !!!~~~~~DONE~~~~~!!!")