import spacy

_POS_ = {'ADJ','ADV','INTJ','NOUN','PROPN','VERB'}

class EnrichQuery():

	def enrich(self,querystring):
		if "q" in querystring:
			doc = self.nlp(querystring["q"])
			terms = []
			for tok in doc:
				if (tok.is_alpha) and (len(tok.lemma_)>0) and (tok.pos_ in _POS_):
					terms.append(tok.lemma_ + tok.whitespace_)
				else:
					terms.append(tok.text_with_ws)
			enriched = ''.join(terms)
		return enriched

	def __init__(self,model='en_core_web_lg'):
		self.nlp = spacy.load(model)