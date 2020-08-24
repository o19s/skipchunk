from sq import SkipchunkQuery

q = SkipchunkQuery('http://localhost:8983/solr/','osc-blog')

q.explore("solr")
q.explore("elast")
q.explore("relev")
q.explore("training")
q.explore("search")
q.explore("engine")
q.explore("learning")
q.explore("syn")
q.explore("taxo")
q.explore("term")
q.explore("luce")