# -*- coding: utf-8 -*-

"""Main module."""

import os
import shutil
import collections
import spacy
import pickle
import datetime
import sq
from datetime import date as dt
from enum import Enum
from tqdm import tqdm
from nltk.corpus import wordnet as wn

#### TODO: make these tag sets configurable!
_NNJJ_ = {'JJ','JJR','JJS','NN','NNP','NNS','ADJ','NOUN'} #Nouns and Adjectives
_VBRB_ = {'RB','RBR','RBS','RP','VB','VBD','VBG','VBN','VBP','VBZ','ADV','VERB'} #Verbs and Adverbs
_PUNC_ = {'.',',','?','!',';',':','(',')','[',']','{','}','"','\''} #Punctuation

_SUBJ_DEPS_ = {'nsubjpass','nsubj'}
_OBJ_DEPS_ = {'dobj'}

_EXCL_ = {'SP','-RRB-','HYPH'} #Noise to skip
_EXCL_DEPS_ = {} #dependencies to exclude


def lemmatize(token):
    lemma = token.lower_
    if token.tag_ in _NNJJ_:
        lemma = token.lemma_
    elif token.tag_ in _VBRB_:
        lemma = token.lemma_
    return lemma

def adj_to_noun(lem):
    for i in wn.synsets(lem, wn.ADJ):
        for j in i.lemmas():
            drf = j.derivationally_related_forms()
            drf.sort(key = lambda x: len(x.name()))
            for k in drf:
                if k.name()[:2] == lem[:2]:
                    #Found it!
                    return k.name()

def noun_to_adj(lem):
    for i in wn.synsets(lem, wn.NOUN):
        for j in i.lemmas():
            for k in j.derivationally_related_forms():
                if k.name()[:2] == lem[:2]:
                    #Found it!
                    return k.name()

# ------------------------------------------------------
# Extracts and annotates terms from a spacy document (preferrably a sentence)

## An annotated term
class Term:

    def useDerivedForm(self):
        if self.derived is not None:
            self.override = self.derived
        else:
            self.text = self.lemma

    def useLemmaForm(self):
        self.text = self.lemma

    def clone(self):
        return Term(
            self.norm,
            self.lemma,
            self.tag,
            self.dep,
            self.derived,
            _text=self.text,
            _override=self.override,
            _objectOf=self.objectOf,
            _subjectOf=self.subjectOf
            )

    def __init__(self,_norm="",_lemma="",_tag="",_dep="",_derived=None,_text=None,_override=None,_objectOf=None,_subjectOf=None):
        self.text = _norm #Default the label to the original form.  This may become the lemma based on logic
        self.norm = _norm  #The original form of the word
        self.lemma = _lemma #The lemmatized form of the word
        self.tag = _tag #The part of speech tag
        self.dep = _dep #The dependency
        self.derived = _derived #the derived form (typical de-adjectival nouns)
        self.override = _override #This may become the derived form based on logic
        self.objectOf = _objectOf #If the term is a direct object, this is the normalized ancestor verb
        self.subjectOf = _subjectOf #If the term is a nominal subject, this is the normalized ancestor verb

## The annotation method adds contextual information to a token
def tokenToTerm(tok):
    term = None

    if (tok.tag_ not in _EXCL_):
        lemma = lemmatize(tok)
        drf = None
        objectOf = None
        subjectOf = None
        
        #Derive related form:
        if (tok.tag_ == 'JJ'):
            drf = adj_to_noun(lemma)

        #Parent verb for objects:
        if (tok.dep_ in _OBJ_DEPS_) and (tok.head.tag_ in _VBRB_):
            objectOf = tok.head.lemma_

        #Parent verb for subjects:
        if (tok.dep_ in _SUBJ_DEPS_) and (tok.head.tag_ in _VBRB_):
            subjectOf = tok.head.lemma_

        term = Term(tok.norm_, lemma, tok.tag_, tok.dep_, drf, _objectOf=objectOf, _subjectOf=subjectOf)
                
    return term

# ------------------------------------------------------
# Normalizes chunked terms to well-formed concept labels

class Label:

    @staticmethod
    def makeKey(vals):
        return '_'.join(sorted(vals)).lower()

    @staticmethod
    def makeIdiom(vals):
        return '_'.join(vals).lower()

    @staticmethod
    def makeLabel(vals):
        return ' '.join(vals).lower()

    def __init__(self,_keys=[],_idioms=[],_labels=[],_start=-1,_end=-1,_docid=-1,_sentenceid=-1,_objectOf=None,_subjectOf=None):
        self.key = Label.makeKey(_keys)
        self.idiom = Label.makeIdiom(_idioms)
        self.label = Label.makeLabel(_labels)
        self.length = len(_labels)
        self.start = _start
        self.end = _end
        self.docid = _docid
        self.sentenceid = _sentenceid
        self.objectOf = _objectOf
        self.subjectOf = _subjectOf

#Converts the chunk to a Label
def chunkToLabel(stack,origs,start,docid,sentenceid,type="concept"):
    keys = []
    idioms = []
    labels = []

    objectOf = None
    subjectOf = None
    
    #Make the key from only nouns, adjectives, verbs, and adverbs
    #An override can be set to the token (usually a derived related form, such as a deadjectival noun)
    #Idioms are also made by removing punctuation
    for tok in stack:
        val = tok.text

        if tok.override is not None:
            val = tok.override
        
        if tok.tag in _NNJJ_ or tok.tag in _VBRB_:
            keys.append(val)
        
        if val not in _PUNC_:
            idioms.append(val)

        if tok.objectOf:
            objectOf = tok.objectOf

        if tok.subjectOf:
            subjectOf = tok.subjectOf


    #Removes punctuation from the label
    # 
    i = 0
    j = 0
    k = 0
    f = False
    for tok in origs:

        j += 1

        #if tok.text not in _PUNC_:
        labels.append(tok.text)

        if tok.tag in _NNJJ_ or tok.tag in _VBRB_:
            i = j
            if not f:
                k = j-1
            f = True

    labels = labels[k:i]
    
    return Label(keys,idioms,labels,_start=start+k,_end=start+i,_docid=docid,_sentenceid=sentenceid,_objectOf=objectOf,_subjectOf=subjectOf)

# ------------------------------------------------------
def skipchunk(sentence,docid,sentenceid,maxslop=4,minlength=2,maxlength=4):

    stack = []
    origs = []
    
    isconcept = False    
    concepts = []

    ispredicate = False
    predicates = []

    i = 0
    start = 0
    last = 0
    slop = 0

    for token in sentence:

        term = tokenToTerm(token)

        if term:

            if (term.tag in _NNJJ_):
                if ispredicate:
                    predicate = chunkToLabel(stack,origs,start,docid,sentenceid)
                    predicates.append(predicate)
                    stack=[]
                    origs=[]
                
                last  = 0
                start = i
                ispredicate = False
                isconcept = True
                stackItem = term.clone()
                stackItem.useDerivedForm()
                stack.append(stackItem)
                origs.append(term)

                if len(stack)>=maxlength:
                    concept = chunkToLabel(stack,origs,start,docid,sentenceid)
                    concepts.append(concept)
                    stack=[]
                    origs=[]                

            elif (term.tag in _VBRB_) and (term.dep not in _EXCL_DEPS_):
                if isconcept:
                    concept = chunkToLabel(stack,origs,start,docid,sentenceid)
                    concepts.append(concept)
                    stack=[]
                    origs=[]
                    
                last  = 0
                start = i
                ispredicate = True
                isconcept = False
                stackItem = term.clone()
                stackItem.useLemmaForm()
                stack.append(stackItem)                
                origs.append(term)

            elif (isconcept):
                slop += 1
                last += 1

                origs.append(term)

                if ((slop>maxslop) or (term.norm in _PUNC_)):
                    concept = chunkToLabel(stack,origs,start,docid,sentenceid)
                    concepts.append(concept)
                    stack=[]
                    origs=[]
                    isconcept = False

            elif (ispredicate):
                slop += 1
                last += 1

                origs.append(term)

                if ((slop>maxslop) or (term.norm in _PUNC_) or (term.dep in _EXCL_DEPS_)):
                    predicate = chunkToLabel(stack,origs,start,docid,sentenceid)
                    predicates.append(predicate)
                    stack=[]
                    origs=[]
                    ispredicate = False

        #else:
        #    stack = []
        #    origs = []          
        #    isconcept = False    
        #    ispredicate = False
        #    start = 0
        #    last = 0
        #    slop = 0

        i += 1

    return concepts,predicates


# --------------------------------------------------
# Merges Labels with the same key into Concept Groups
class ConceptGroup:

    def alternate(self,_label,_count):
        if (_label not in self.alternates):
            self.alternates[_label] = 0
        self.alternates[_label] += _count

    def addlabels(self,_labels):
        self.labels = _labels

    def __init__(self,_key,_total,_preflabel,_prefcount):
        self.key = _key
        self.total = _total
        self.preflabel = _preflabel
        self.prefcount = _prefcount
        self.alternates = {}
        self.labels = {}

def groupConcepts(data,minlabels=1):
    items = []
    for key in data.keys():
        labels = data[key]
        if len(labels)>=minlabels:

            group = None
            preflabel = None

            # Get the label frequency
            aggregate = collections.Counter(map(lambda x:x.label,labels))
            
            for c in aggregate.most_common():
                label = c[0]
                count = c[1]
                if not preflabel:
                    preflabel = label
                    prefcount = count
                    group = ConceptGroup(key,len(labels),preflabel,prefcount)

                if group:
                    group.alternate(label,count)

            if group:
                group.addlabels(labels)

            items.append(group)
    return sorted(items, key=lambda x:x.total, reverse=True)

##==========================================================
# MAIN API ENTRY POINT!  USE THIS!

class Skipchunk():

    # --------------------------------------------------

    def enrich(self,tuples):

        idfield = self.idfield
        maxslop = self.maxslop
        minconceptlength = self.minconceptlength
        maxconceptlength = self.maxconceptlength
        minpredicatelength = self.minpredicatelength
        maxpredicatelength = self.maxpredicatelength
        minlabels = self.minlabels
        concepts = self.concepts
        predicates = self.predicates
        
        enriched = []

        for doc,context in self.nlp.pipe(tuples,as_tuples=True):

            rich = context
            docid = context[idfield]

            sentenceid = 0

            docconcepts = {}
            docpredicates = {}

            for sentence in doc.sents:

                cons,preds = skipchunk(sentence,docid=docid,sentenceid=sentenceid,maxslop=maxslop,maxlength=maxconceptlength)

                for concept in cons:
                    if concept.length>=minconceptlength:
                        if concept.key not in concepts:
                            concepts[concept.key] = []
                        concepts[concept.key].append(concept)

                        if concept.key not in docconcepts:
                            docconcepts[concept.key] = []
                        docconcepts[concept.key].append(concept)

                for predicate in preds:
                    if predicate.length>=minpredicatelength:
                        if predicate.key not in predicates:
                            predicates[predicate.key] = []
                        predicates[predicate.key].append(predicate)
                        if predicate.key not in docpredicates:
                            docpredicates[predicate.key] = []
                        docpredicates[predicate.key].append(predicate)

                sentenceid += 1

            rich["skipchunk_concepts"] = docconcepts
            rich["skipchunk_predicates"] = docpredicates
            enriched.append(rich)

        conceptgroups = groupConcepts(concepts,minlabels=minlabels)
        predicategroups = groupConcepts(predicates,minlabels=minlabels)

        self.enriched = enriched
        self.concepts = concepts
        self.predicates = predicates
        self.conceptgroups = conceptgroups
        self.predicategroups = predicategroups

        return enriched,concepts,predicates,conceptgroups,predicategroups

    # --------------------------------------------------

    def load(self,path=None):

        if not path:
            path = self.pickle_data

        if os.path.isdir(path):
            with open(os.path.join(path,'enriched_posts.pickle'),'rb') as fd:
                self.enriched = pickle.load(fd)

            with open(os.path.join(path,'concepts_posts.pickle'),'rb') as fd:
                self.concepts = pickle.load(fd)

            with open(os.path.join(path,'predicates_posts.pickle'),'rb') as fd:
                self.predicates = pickle.load(fd)

            with open(os.path.join(path,'conceptgroups_posts.pickle'),'rb') as fd:
                self.conceptgroups = pickle.load(fd)

            with open(os.path.join(path,'predicategroups_posts.pickle'),'rb') as fd:
                self.predicategroups = pickle.load(fd)

    # --------------------------------------------------

    def save(self,path=None):

        if not path:
            path = self.pickle_data

        if os.path.isdir(path):
            with open(os.path.join(path,'enriched_posts.pickle'),'wb') as fd:
                pickle.dump(self.enriched,fd,protocol=pickle.HIGHEST_PROTOCOL)

            with open(os.path.join(path,'concepts_posts.pickle'),'wb') as fd:
                pickle.dump(self.concepts,fd,protocol=pickle.HIGHEST_PROTOCOL)

            with open(os.path.join(path,'predicates_posts.pickle'),'wb') as fd:
                pickle.dump(self.predicates,fd,protocol=pickle.HIGHEST_PROTOCOL)

            with open(os.path.join(path,'conceptgroups_posts.pickle'),'wb') as fd:
                pickle.dump(self.conceptgroups,fd,protocol=pickle.HIGHEST_PROTOCOL)

            with open(os.path.join(path,'predicategroups_posts.pickle'),'wb') as fd:
                pickle.dump(self.predicategroups,fd,protocol=pickle.HIGHEST_PROTOCOL)

    def __init__(self,
        name,
        spacy_model='en_core_web_lg',
        idfield='id',
        maxslop=4,
        minconceptlength=2,
        maxconceptlength=4,
        minpredicatelength=2,
        maxpredicatelength=4,
        minlabels=2,
        concept_tags = _NNJJ_,
        predicate_tags = _VBRB_,
        punctuation_tags = _PUNC_,
        subjectof_dependencies = _SUBJ_DEPS_,
        objectof_dependencies = _OBJ_DEPS_,
        exclude_tags = _EXCL_,
        exclude_dependencies = _EXCL_DEPS_
        ):

        #Config:
        self.name = name
        self.spacy_model=spacy_model
        self.nlp = spacy.load(self.spacy_model)
        self.idfield = idfield
        self.maxslop = maxslop
        self.minconceptlength = minconceptlength
        self.maxconceptlength = maxconceptlength
        self.minpredicatelength = minpredicatelength
        self.maxpredicatelength = maxpredicatelength
        self.minlabels = minlabels

        #These don't do anything yet but they will be used later to untangle the global constants
        self.concept_tags = concept_tags
        self.predicate_tags = predicate_tags
        self.punctuation_tags = punctuation_tags
        self.subjectof_dependencies = subjectof_dependencies
        self.objectof_dependencies = objectof_dependencies
        self.exclude_tags = exclude_tags
        self.exclude_dependencies = exclude_dependencies

        #Stateful data that will change when Skipchunk.enrich is run:
        self.enriched = None
        self.concepts = dict()
        self.predicates = dict()
        self.conceptgroups = None
        self.predicategroups = None

        #Where we will keep stuff:
        self.skipchunk_data = os.path.join(os.getcwd(),'skipchunk_data')
        if not os.path.isdir(self.skipchunk_data):
            os.makedirs(self.skipchunk_data)

        self.root = os.path.join(self.skipchunk_data, name)
        if not os.path.isdir(self.root):
            os.makedirs(self.root)

        self.pickle_data = os.path.join(self.root, 'pickle')
        if not os.path.isdir(self.pickle_data):
            os.makedirs(self.pickle_data)

        self.solr_data = os.path.join(self.root, 'solr')
        if not os.path.isdir(self.solr_data):
            #Create configset and root path for data for the new solr core
            module_dir = os.path.dirname(sq.__file__)
            pathlen = module_dir.rfind('/')+1
            source = module_dir[0:pathlen] + '/solr_home/configsets/skipchunk-configset'
            shutil.copytree(source,self.solr_data)

##==========================================================
## EASY SANITY TESTING:
## python skipchunk.py

if __name__ == "__main__":
    import jsonpickle
    def pretty(obj):
        print(jsonpickle.encode(obj,indent=2))

    def test():

        text = 'The quick brown fox jumped over the lazy dog.  I ate a sandwich in the afternoon, then I drank some tea.  That afternoon\'s sandwich was very tasty.  So was the tea.'
        post = {"id":"123","text":text}
        pairs = [(text,post)]
        print(pairs)

        sc = Skipchunk('junk',
            spacy_model='en_core_web_sm',
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

    test()