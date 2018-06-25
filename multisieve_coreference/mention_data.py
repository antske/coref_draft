"""
This module parses the term layer of a KAF/NAF object
"""
from __future__ import print_function
import os

from .offset_info import (
    convert_term_ids_to_offsets,
    get_offset,
    get_offsets_from_span,
    get_pos_of_term,
)

stop_words = []


def initiate_stopword_list(lang='nl'):

    global stop_words
    resources = os.path.abspath(os.path.join(os.path.dirname(__file__), "resources"))

    stopfile = open(os.path.join(resources, lang, 'stop_words.txt'),'r')
    for line in stopfile:
        stop_words.append(line.rstrip())

    stopfile.close()



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
        self.id = mid   # confirmed
        # becomes dictionary mapping token to string for creating the surface
        # of substrings
        self.span = span
        self.number = ''
        self.gender = ''
        self.person = ''
        self.head_id = head_id
        self.full_head = []
        self.head_pos = head_pos
        self.relaxed_span = []
        self.in_coref_class = []    # confirmed
        self.entity_type = None
        self.in_quotation = False
        self.relative_pron = False
        self.reflective_pron = False
        self.coreference_prohibited = []
        self.begin_offset = ''
        self.end_offset = ''
        self.modifiers = []
        self.appositives = []
        self.predicatives = []
        self.no_stop_words = []
        self.main_modifiers = []
        self.sentence_number = ''

    def __repr__(self):
        return self.__class__.__name__ + '(' + \
            'id={!r}, '.format(self.id) + \
            'span={!r}, '.format(self.span) + \
            'number={!r}, '.format(self.number) + \
            'gender={!r}, '.format(self.gender) + \
            'person={!r}, '.format(self.person) + \
            'head_id={!r}, '.format(self.head_id) + \
            'full_head={!r}, '.format(self.full_head) + \
            'head_pos={!r}, '.format(self.head_pos) + \
            'relaxed_span={!r}, '.format(self.relaxed_span) + \
            'in_coref_class={!r}, '.format(self.in_coref_class) + \
            'entity_type={!r}, '.format(self.entity_type) + \
            'in_quotation={!r}, '.format(self.in_quotation) + \
            'relative_pron={!r}, '.format(self.relative_pron) + \
            'reflective_pron={!r}, '.format(self.reflective_pron) + \
            'coreference_prohibited={!r}, '.format(self.coreference_prohibited) + \
            'begin_offset={!r}, '.format(self.begin_offset) + \
            'end_offset={!r}, '.format(self.end_offset) + \
            'modifiers={!r}, '.format(self.modifiers) + \
            'appositives={!r}, '.format(self.appositives) + \
            'predicatives={!r}, '.format(self.predicatives) + \
            'no_stop_words={!r}, '.format(self.no_stop_words) + \
            'main_modifiers={!r}, '.format(self.main_modifiers) + \
            'sentence_number={!r}, '.format(self.sentence_number) +  \
            ')'

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

    def set_head_id(self, hid):
        self.head_id = hid

    def get_head_id(self):
        return self.head_id

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

    def set_relative_pronoun(self, bool):

        self.relative_pron = bool

    def is_relative_pronoun(self):

        return self.relative_pron

    def set_reflective_pronoun(self, bool):

        self.reflective_pron = bool

    def is_reflective_pronoun(self):

        return self.reflective_pron

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

    def set_predicatives(self, preds):

        self.predicatives = preds

    def add_predicative(self, pred):

        self.predicatives.append(pred)

    def get_predicatives(self):

        return self.predicatives

    def set_no_stop_words(self, nsw):

        self.no_stop_words = nsw

    def add_no_stop_word(self, nsw):

        self.no_stop_words.append(nsw)

    def get_no_stop_words(self):

        return self.no_stop_words

    def set_main_modifiers(self, mmods):

        self.main_modifiers = mmods

    def add_main_modifier(self, mmod):

        self.main_modifiers.append(mmod)

    def get_main_modifiers(self):

        return self.main_modifiers

    def set_sentence_number(self, sentnr):

        self.sentence_number = sentnr

    def get_sentence_number(self):

        return self.sentence_number


class Cmentions:
    '''
    This class covers information about the collection of coreference mentions as a whole
    '''

    def __init__(self, mentions=None, final_id='m0'):
        '''
        Constructor for mentions object
        '''
        self.mentions = mentions if mentions is not None else []
        self.final_id = final_id


def create_mention(nafobj, constituentInfo, head, mid):
    '''
    Function that creates mention object from naf information
    :param nafobj: the input naffile
    :param span: the mention span
    :param span: the id of the constituent's head
    :param idnr: the idnr (for creating a unique mention id
    :return:
    '''

    if head is None:
        head_id = head
    else:
        head_id = get_offset(nafobj, head)

    span = constituentInfo.span
    offset_ids_span = convert_term_ids_to_offsets(nafobj, span)
    mention = Cmention(mid, span=offset_ids_span, head_id=head_id)
    sentence_number = get_sentence_number(nafobj, head)
    mention.set_sentence_number(sentence_number)
    # add no stop words and main modifiers
    add_non_stopwords(nafobj, span, mention)
    add_main_modifiers(nafobj, span, mention)
    # mwe info
    full_head_tids = constituentInfo.multiword
    full_head_span = convert_term_ids_to_offsets(nafobj, full_head_tids)
    mention.set_full_head(full_head_span)
    # modifers and appositives:
    relaxed_span = offset_ids_span
    for mod_in_tids in constituentInfo.modifiers:
        mod_span = convert_term_ids_to_offsets(nafobj, mod_in_tids)
        mention.add_modifier(mod_span)
        for mid in mod_span:
            if mid > head_id and mid in relaxed_span:
                relaxed_span.remove(mid)
    for app_in_tids in constituentInfo.appositives:
        app_span = convert_term_ids_to_offsets(nafobj, app_in_tids)
        mention.add_appositive(app_span)
        for mid in app_span:
            if mid > head_id and mid in relaxed_span:
                relaxed_span.remove(mid)
    mention.set_relaxed_span(relaxed_span)

    for pred_in_tids in constituentInfo.predicatives:
        pred_span = convert_term_ids_to_offsets(nafobj, pred_in_tids)
        mention.add_predicative(pred_span)

    # set sequence of pos FIXME: if not needed till end; remove
    # os_seq = get_pos_of_span(nafobj, span)
    # mention.set_pos_seq(pos_seq)
    # set pos of head
    if head is not None:
        head_pos = get_pos_of_term(nafobj, head)
        mention.set_head_pos(head_pos)
        if head_pos in ['pron', 'noun', 'name']:
            analyze_nominal_information(nafobj, head, mention)

    begin_offset, end_offset = get_offsets_from_span(nafobj, span)
    mention.set_begin_offset(begin_offset)
    mention.set_end_offset(end_offset)

    return mention


def add_main_modifiers(nafobj, span, mention):
    '''
    Function that creates list of all modifiers that are noun or adjective (possibly including head itself)
    :param nafobj: input naf
    :param span: list of term ids
    :param mention: mention object
    :return:
    '''

    main_mods = []
    for tid in span:
        term = nafobj.get_term(tid)
        if term.get_pos() in ['adj','noun']:
            main_mods.append(tid)

    main_mods_offset = convert_term_ids_to_offsets(nafobj, main_mods)
    mention.set_main_modifiers(main_mods_offset)


def add_non_stopwords(nafobj, span, mention):
    '''
    Function that verifies which terms in span are not stopwords and adds these to non-stop-word list
    :param nafobj: input naf (for linguistic information)
    :param span: list of term ids
    :param mention: mention object
    :return:
    '''
    non_stop_terms = []

    for tid in span:
        my_term = nafobj.get_term(tid)
        if not my_term.get_type() == 'closed' and not my_term.get_lemma().lower() in stop_words:
            non_stop_terms.append(tid)

    non_stop_span = convert_term_ids_to_offsets(nafobj, non_stop_terms)
    mention.set_no_stop_words(non_stop_span)


def analyze_nominal_information(nafobj, term_id, mention):

    myterm = nafobj.get_term(term_id)
    morphofeat = myterm.get_morphofeat()
    identify_and_set_person(morphofeat, mention)
    identify_and_set_gender(morphofeat, mention)
    identify_and_set_number(morphofeat, myterm, mention)
    set_is_relative_pronoun(morphofeat, mention)


def get_sentence_number(nafobj, head):

    myterm = nafobj.get_term(head)
    tokid = myterm.get_span().get_span_ids()[0]
    mytoken = nafobj.get_token(tokid)
    sent_nr = int(mytoken.get_sent())

    return sent_nr


def identify_and_set_person(morphofeat, mention):

    if '1' in morphofeat:
        mention.set_person('1')
    elif '2' in morphofeat:
        mention.set_person('2')
    elif '3' in morphofeat:
        mention.set_person('3')


def identify_and_set_number(morphofeat, myterm, mention):

    if 'ev' in morphofeat:
        mention.set_number('ev')
    elif 'mv' in morphofeat:
        mention.set_number('mv')
    elif 'getal' in morphofeat:
        lemma = myterm.get_lemma()
        if lemma in ['haar', 'zijn', 'mijn', 'jouw', 'je']:
            mention.set_number('ev')
        elif lemma in ['ons', 'jullie', 'hun']:
            mention.set_number('mv')


def identify_and_set_gender(morphofeat, mention):

    if 'fem' in morphofeat:
        mention.set_gender('fem')
    elif 'masc' in morphofeat:
        mention.set_gender('masc')
    elif 'onz,' in morphofeat:
        mention.set_gender('neut')


def set_is_relative_pronoun(morphofeat, mention):

    if 'betr,' in morphofeat:
        mention.set_relative_pronoun(True)
    if 'refl,' in morphofeat:
        mention.set_reflective_pronoun(True)
