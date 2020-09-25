# Skipchunk

[![Pypi](https://img.shields.io/pypi/v/skipchunk.svg)](https://pypi.python.org/pypi/skipchunk)

[![Travis build status](https://img.shields.io/travis/binarymax/skipchunk.svg)](https://travis-ci.org/binarymax/skipchunk)

[![Documentation Status](https://readthedocs.org/projects/skipchunk/badge/?version=latest)](https://skipchunk.readthedocs.io/en/latest/?badge=latest)

Easy natural language concept search for the masses.

Out of the box it provides a hassle-free autosuggest for any corpus from scratch, and latent knowledge graph extraction and exploration.

* Free software: Apache 2.0 license
* Documentation: https://skipchunk.readthedocs.io.

## Install

```bash
pip install skipchunk
python -m spacy download 'en_core_web_lg'
python -m nltk.downloader wordnet
```

You also need to have Solr or Elasticsearch installed and running somewhere!  The current supported version is 8.4.1, but it might work on other versions.

## Use It!

See the ```./example/``` folder for an end-to-end OSC blog load and query


## Features

* Identifies all the noun phrases and verb phrases in a corpus
* Indexes these phrases in Solr for a really good out-of-the-box autosuggest
* Structures the phrases as a graph so that concept-relationship-concept can be easily found
* Keeps enriched content ready for reindexing

## Credits

Developed by Max Irwin, OpenSourceConnections https://opensourceconnections.com

All the blog posts contained in the example directory are copyright OpenSource Connections, and may not be redistributed without permission