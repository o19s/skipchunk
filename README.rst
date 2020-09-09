=========
skipchunk
=========


.. image:: https://img.shields.io/pypi/v/skipchunk.svg
        :target: https://pypi.python.org/pypi/skipchunk

.. image:: https://img.shields.io/travis/binarymax/skipchunk.svg
        :target: https://travis-ci.org/binarymax/skipchunk

.. image:: https://readthedocs.org/projects/skipchunk/badge/?version=latest
        :target: https://skipchunk.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


Easy natural language concept search for the masses.

Skipchunk is a text preprocessor for search.  It uses NLP (via spacy) to fix the naive normalization issues in Solr and Elasticsearch analysis chains.

Out of the box it provides a hassle-free autosuggest for any corpus from scratch.

* Free software: Apache 2.0 license
* Documentation: https://skipchunk.readthedocs.io.

Install
-------

``
pip install skipchunk
python -m spacy download 'en_core_web_lg'
python
>>>import nltk
>>>nltk.download()  ##When the GUI opens, install the 'wordnet' package listed in the 'all packages' tab
>>>^D ##quit python after wordnet is downloaded
``

You also need to have solr installed and running somewhere!  The current supported version is 8.4.1, but it might work on other versions.

Use It!
-------
See the ``./example/`` folder for an end-to-end OSC blog load and query


Features
--------

* Identifies all the noun phrases and verb phrases in a corpus
* Indexes these phrases in Solr for a really good out-of-the-box autosuggest
* Structures the phrases as a graph so that concept-relationship-concept can be easily found
* Keeps enriched content ready for reindexing

Credits
-------

Developed by Max Irwin, OpenSourceConnections https://opensourceconnections.com

Heavily uses https://spacy.io - credit to the https://explosion.ai team!
Dependent on Solr (an Apache project) https://lucene.apache.org/solr

All the blog posts contained in the example directory are copyright OpenSource Connections, and may not be redistributed without permission