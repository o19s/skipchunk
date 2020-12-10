# Skipchunk

[![Pypi](https://img.shields.io/pypi/v/skipchunk.svg)](https://pypi.python.org/pypi/skipchunk)

[![Travis build status](https://img.shields.io/travis/binarymax/skipchunk.svg)](https://travis-ci.org/binarymax/skipchunk)

[![Documentation Status](https://readthedocs.org/projects/skipchunk/badge/?version=latest)](https://skipchunk.readthedocs.io/en/latest/?badge=latest)

Easy search autosuggest with NLP magic.

Out of the box it provides a hassle-free autosuggest for any corpus from scratch, and latent knowledge graph extraction and exploration.

* Free software: MIT License
* Documentation: https://skipchunk.readthedocs.io.

## Install

```bash
pip install skipchunk
python -m spacy download 'en_core_web_lg'
python -m nltk.downloader wordnet
```

You also need to have Solr or Elasticsearch installed and running somewhere!

The current Solr supported version is 8.4.1, but it might work on other versions.

The current Elasticsearch supported version is 7.6.2, but it might work on other versions.

## Use It!

See the ```./example/``` folder for an end-to-end OSC blog load:

### Solr

Start Solr first!  Doesn't work with Solr cloud yet, but we're working on it.
You'll need to start solr using skipchunk's solr_home directory for now.

Then run this: ```python solr-blog-example.py```

### Elasticsearch

Start Elasticsearch first!

Then run this: ```python elasticsearch-blog-example.py```

## Features

* Identifies and groups the noun phrases and verb phrases in a corpus
* Indexes these phrases in Solr or Elasticsearch for a really good out-of-the-box autosuggest
* Structures the phrases as a graph so that concept-relationship-concept can be easily found
* Meant to handle batched updates as part of a full stack search platform

## Library API

### Engine configuration

You need an engine_config, as a dict, to create skipchunk.
The dict must contain the following entries

- host (the fully qualified URL of the engine web API endpoint)
- name (the name of the graph)
- path (the on-disk location of stateful data that will be kept)
- engine_name (either "solr" or "elasticsearch")

#### Solr engine config example

```python
    engine_config_solr = {
        "host":"http://localhost:8983/solr/",
        "name":"osc-blog",
        "path":"./skipchunk_data",
        "engine_name":"solr"
    }
```

#### Elasticsearch engine config example
```python
    engine_config_elasticsearch = {
        "host":"http://localhost:9200/",
        "name":"osc-blog",
        "path":"./skipchunk_data",
        "engine_name":"elasticsearch"
    }
```

### Skipchunk Initialization

When initializing Skipchunk, you will need to provide the constructor with the following parameters

- engine_config (the dict containing search engine connection details)
- spacy_model="en_core_web_lg" (the spacy model to use to parse text)
- minconceptlength=1 (the minimum number of words that can appear in a noun phrase)
- maxconceptlength=3 (the maximum number of words that can appear in a noun phrase)
- minpredicatelength=1 (the minimum number of words that can appear in a verb phrase)
- maxpredicatelength=3 (the maximum number of words that can appear in a verb phrase)
- minlabels=1 (the number of times a concept/predicate must appear before it is recognized and kept.  The lower this number, the more concepts will be kept - so be careful with large content sets!)
- cache_documents=False
- cache_pickle=False

### Skipchunk Methods

- ```tuplize(filename=source,fields=['title','content',...])``` (Produces a list of (text,document) tuples ready for processing by the enrichment.)
- ```enrich(tuples)``` (Enriching can take a long time if you provide lots of text.  Consider batching at 10k docs at a time.)
- ```save``` (Saves to pickle)
- ```load``` (Loads from pickle)

### Graph API

After enrichment, you can then index the graph into the engine

- ```index(skipchunk:Skipchunk)``` (Updates the knowledge graph in the search engine)
- ```delete``` (Deletes a knowledge graph - be careful!)

After indexing, you can call these methods to get autocompleted concepts or walk the knowledge graph

- ```conceptVerbConcepts(concept:str,verb:str,mincount=1,limit=100) -> list``` ( Accepts a verb to find the concepts appearing in the same context)
- ```conceptsNearVerb(verb:str,mincount=1,limit=100) -> list``` ( Accepts a verb to find the concepts appearing in the same context)
- ```verbsNearConcept(concept:str,mincount=1,limit=100) -> list``` ( Accepts a concept to find the verbs appearing in the same context)
- ```suggestConcepts(prefix:str,build=False) -> list``` ( Suggests a list of concepts given a prefix)
- ```suggestPredicates(prefix:str,build=False) -> list``` ( Suggests a list of predicates given a prefix)
- ```summarize(mincount=1,limit=100) -> list``` ( Summarizes a core)
- ```graph(subject:str,objects=5,branches=10) -> list``` ( Gets the subject-predicate-object neighborhood graph for a subject)

## Credits

Developed by Max Irwin, OpenSource Connections https://opensourceconnections.com

All the blog posts contained in the example directory are copyright OpenSource Connections, and may not be used nor redistributed without permission