"""
This module parses the term layer of a KAF/NAF object
"""
from __future__ import print_function


class Cmention:
    '''
    This class covers information about mentions that is relevant for coreference resoltion
    '''

    def __init__(self, mid, span=[], head_id=None, head_pos=None):
        '''
        Constructor of the mention
        #TODO: revise so that provides information needed for some sieve;
        #STEP 1: seive 3 needs option to remove post-head modifiers
        '''
        self.id = mid #confirmed
        self.span = span #becomes dictionary mapping token to string for creating the surface of substrings
        self.number = ''
        self.gender = ''
        self.person = ''
        self.head_id = head_id
        self.full_head = []
        self.head_pos = head_pos
        self.relaxed_span = []
        self.in_coref_class = [] #confirmed
        self.entity_type = None
        self.in_quotation = False
        self.coreference_prohibited = []
        self.begin_offset = ''
        self.end_offset = ''
        self.modifiers = []
        self.appositives = []

    def set_span(self, span):

        self.span = span

    def get_span(self):

        return self.span

    def set_person(self, person):
        self.person = person

    def get_person(self):
        return self.person

    def set_number(self, number):
        self.number = number

    def get_number(self):
        return self.number

    def set_gender(self, gender):
        self.gender = gender

    def get_gender(self):
        return self.gender

    def set_full_head(self, full_head):

        self.full_head = full_head

    def get_full_head(self):

        return self.full_head

    def set_relaxed_span(self, relaxed_span):

        self.relaxed_span = relaxed_span

    def add_relaxed_span_id(self, rsid):

        self.relaxed_span.append(rsid)

    def get_relaxed_span(self):

        return self.relaxed_span

    def set_head_pos(self, head_pos):

        self.head_pos = head_pos

    def get_head_pos(self):

        return self.head_pos

    def set_entity_type(self, etype):

        self.entity_type = etype

    def get_entity_type(self):

        return self.entity_type

    def set_in_coref_class(self, coref_id):

        self.in_coref_class.append(coref_id)

    def get_in_coref_class(self):

        return self.in_coref_class

    def set_begin_offset(self, boffset):

        self.begin_offset = boffset

    def get_begin_offset(self):

        return self.begin_offset

    def set_end_offset(self, eoffset):

        self.end_offset = eoffset

    def get_end_offset(self):

        return self.end_offset

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



class Cmentions:
    '''
    This class covers information about the collection of coreference mentions as a whole
    '''

    def __init__(self, mentions = [], final_id='m0'):
        '''
        Constructor for mentions object
        '''
        self.mentions = mentions
        self.final_id = final_id


class Cquotation:
    '''
    This class encodes source and quotation
    '''

    def __init__(self, sip):
        '''
        Constructor for quotations object
        '''
        self.sip = sip
        self.span = []
        self.string = ''
        self.beginOffset = ''
        self.endOffset = ''
        self.source = ''
        self.addressee = ''
        self.topic = ''

    def set_span(self, span):

        self.span = span

    def get_span(self):

        return self.span

    def set_string(self, mystring):

        self.string = mystring

    def get_string(self):

        return self.string

    def set_begin_offset(self, boffset):

        self.beginOffset = boffset

    def get_begin_offset(self):

        return self.beginOffset

    def set_end_offset(self, eoffset):
        self.endOffset = eoffset

    def get_end_offset(self):
        return self.endOffset

    def set_source(self, source):
        self.source = source

    def get_source(self):
        return self.source

    def set_addressee(self, addressee):
        self.addressee = addressee

    def get_addressee(self):
        return self.addressee

    def set_topic(self, topic):
        self.topic = topic

    def get_topic(self):
        return self.topic

