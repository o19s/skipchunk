from skipchunk import skipchunk
import jsonpickle

def pretty(obj):
    print(jsonpickle.encode(obj,indent=2))

def test():

    skipchunk_config = {
        "host":"http://localhost:9200/",
        "name":"example-sentences",
        "path":"./skipchunk_data",
        "engine_name":"elasticsearch"
    }

    #text = 'The quick brown fox jumped over the lazy dog.  I ate a sandwich in the afternoon, then I drank some tea.  That afternoon\'s sandwich was very tasty.  So was the tea.'
    text = "Some blog posts in Solr were indexed yesterday. They are now available for retrieval."
    post = {"id":"123","text":text}
    pairs = [(text,post)]
    print(pairs)

    sc = skipchunk.Skipchunk(skipchunk_config,
        spacy_model='en_core_web_lg',
        maxslop=3,
        minconceptlength=1,
        maxconceptlength=3,
        minpredicatelength=1,
        maxpredicatelength=3,
        minlabels=1)

    sc.enrich(pairs)
    sc.save()
    sc.load()

    pretty(sc.conceptgroups)
    pretty(sc.predicategroups)

if __name__ == '__main__':
    test()