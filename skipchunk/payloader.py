# -*- coding: utf-8 -*-

"""Payload."""

import spacy

"""
Payloads are assigned to Open Class Words ONLY!

https://universaldependencies.org/docs/u/pos/

Open class words 	Closed class words 	Other
----------------	------------------	-----
ADJ 				ADP 				PUNCT
ADV 				AUX 				SYM
INTJ 				CONJ 				X
NOUN 				DET 	 
PROPN 				NUM 	 
VERB 				PART 	 
  					PRON 	 
  					SCONJ 	 
"""

_POS_SCORES_ = {
	'ADJ'  :  1.5, 	#adjective
    'ADV'  :  1.5, 	#adverb
    'INTJ' :  1.0, 	#interjection
    'NOUN' :  2.5, 	#noun
    'PART' :  1.0, 	#particle
    'PRON' :  1.5, 	#pronoun
    'PROPN':  2.0, 	#proper noun
    'SCONJ':  1.0, 	#subordinating conjunction
    'VERB' :  2.5
}

"""
Part of Speech payloads are cool, but the real juice is from dependencies!
Specifically: subjects, objects, and roots.

The intuition here is because the aboutness of sentences should be considered, not just the mentioning of a concept.
"""

_DEP_SCORES_ = {
	'nsubjpass': 2.0,
	'nsubj'    : 2.0,
	'dobj'     : 2.0,
	'pobj'     : 1.5,
	'root'     : 2.0
}

class Payloader:

	def payload(self,stream):
		
		payloads = []

		for tok in stream:
			score = None

			if tok._pos in self.pos_scores:
				score = self.pos_scores[tok._pos]

				if tok._dep in self.dep_scores:
					score += self.dep_scores[tok._dep]

				payloads.append(tok.text + '|' + str(score))

			else:
				payloads.append(str(tok))

		return payloads

	def __init__(self,pos_scores=_POS_SCORES_,dep_scores=_DEP_SCORES_):
		self.dep_scores = dep_scores
		self.pos_scores = pos_scores