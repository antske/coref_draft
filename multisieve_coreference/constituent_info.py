from collections import defaultdict
from .constituents import get_constituent, head2deps, dep2heads


class Cconstituent_information:
    '''
    This class contains the main constructional information of mentions
    '''

    def __init__(self, head_id, span=None):
        '''
        Constructor for the constituent object
        :param head_id: term id of the head of the constituent
        :param span: list of term ids providing full span of hte constituent
        '''
        self.head_id = head_id
        self.span = span if span is not None else []
        self.multiword = []
        self.modifiers = []
        self.appositives = []
        self.predicatives = []
        self.etype = ''

    def set_span(self, span):

        self.span = span

    def get_span(self):

        return self.span

    def set_multiword(self, mw):

        self.multiword = mw

    def get_multiword(self):

        return self.multiword

    def set_modifiers(self, mods):

        self.modifiers = mods

    def add_modifier(self, mod):

        self.modifiers.append(mod)

    def get_modifiers(self):

        return self.modifiers

    def set_appositives(self, apps):

        self.appositives = apps

    def add_appositive(self, app):

        self.appositives.append(app)

    def get_appositives(self):

        return self.appositives

    def set_predicatives(self, preds):

        self.predicatives = preds

    def add_predicative(self, pred):

        self.predicatives.append(pred)

    def get_predicatives(self):

        return self.predicatives

    def set_etype(self, etype):

        self.etype = etype

    def get_etype(self):

        return self.etype


def get_mwe_and_modifiers_and_appositives(head_id):
    '''
    Function that identifies full mwe head and posthead modifiers
    :param head_id: head_id
    :return: list of full head terms, list of posthead modifiers
    '''

    mwe = [head_id]
    mods = []
    apps = []

    for ID, relation in head2deps.get(head_id, []):
        if relation == 'mwp/mwp':
            mwe.append(head_id)
        elif relation == 'hd/mod':
            dep_constituent = get_constituent(ID)
            mods.append(dep_constituent)
        elif relation == 'hd/app':
            dep_constituent = get_constituent(ID)
            apps.append(dep_constituent)

    return mwe, mods, apps


def get_constituents(mention_heads):

    constituents = {}
    for head in mention_heads:
        mydeps = get_constituent(head)
        myConstituent = Cconstituent_information(head, mydeps)
        mwe, mods, apps = get_mwe_and_modifiers_and_appositives(head)
        myConstituent.set_multiword(mwe)
        myConstituent.set_modifiers(mods)
        myConstituent.set_appositives(apps)
        add_predicative_information(head, myConstituent)
        constituents[head] = myConstituent

    return constituents


def add_predicative_information(head_id, myConstituent):
    '''
    Function that checks if mention is subject in a predicative structure and,
    if so, adds predicative info to constituent object
    :param head_id: identifier of the head of the mention
    :param myConstituent: constituent object
    :return:
    '''

    for headID, headrel in dep2heads.get(head_id, []):
        if headrel == 'hd/su':
            headscomps = head2deps.get(headID)
            for depID, deprel in headscomps:
                if deprel in ['hd/predc', 'hd/predm']:
                    predicative = get_constituent(depID)
                    myConstituent.add_predicative(predicative)


def get_named_entities(nafobj):
    '''
    Function that runs to entity layer and registers named entities
    :param nafobj: the input nafobject
    :return: dictionary of entities, linked to span and entity type
    '''
    entities = {}
    found_spans = []
    for entity in nafobj.get_entities():
        etype = entity.get_type()
        for ref in entity.get_references():
            espan = ref.get_span().get_span_ids()
            head_term = find_head_in_span(espan)
            full_span = get_constituent(head_term)
            myConstituent = Cconstituent_information(head_term, full_span)
            myConstituent.set_multiword(espan)
            mwe, mods, apps = get_mwe_and_modifiers_and_appositives(head_term)
            myConstituent.set_modifiers(mods)
            myConstituent.set_etype(etype)
            myConstituent.set_appositives(apps)
            add_predicative_information(head_term, myConstituent)
            if verify_span_uniqueness(found_spans, espan):

                if head_term not in entities:
                    entities[head_term] = myConstituent
                else:
                    entities[head_term + 'b'] = myConstituent
                found_spans.append(espan)

    return entities


def find_head_in_span(span):
    '''
    Function that return the identifier of the head in the span
    :param span: list of term identiers
    :return: term_id
    '''

    head_term = None
    for term in span:
        constituent = get_constituent(term)
        if set(span) < constituent:
            if head_term is None:
                head_term = term
        #    else:
        #        print('span has more than one head')
    if head_term is None:
        head_term = find_closest_to_head(span)
    return head_term


def find_closest_to_head(span):

    if len(span) == 1:
        return span[0]

    head_term_candidates = defaultdict(list)

    for tid in span:
        if tid in head2deps:
            count = 0
            for deprel in head2deps:
                if deprel[0] in span:
                    count += 1
            head_term_candidates[count].append(tid)
    if len(head_term_candidates) > 0:
        max_deps = sorted(head_term_candidates.keys())[-1]
        best_candidates = head_term_candidates.get(max_deps)
        if len(best_candidates) > 0:
            return best_candidates[0]

    return span[0]


def verify_span_uniqueness(found_spans, span):
    '''
    Function that checks whether entity is not listed twice (bug in
    cltl-spotlight; does not check whether entity has already been found)
    :param found_spans: list of previously found spans
    :param span: current span
    :return: boolean (True if span has not been found before)
    '''

    for fspan in found_spans:
        if len(set(fspan) & set(span)) == len(span):
            return False
    return True
