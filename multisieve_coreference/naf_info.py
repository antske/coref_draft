import os
import logging
from collections import defaultdict

from .mention_data import Cmention, Cquotation
from .naf_classes import get_named_entities, get_constituents
from .quotation_naf import CquotationNaf
from .constituents import (
    get_constituent,
    head2deps,
    dep2heads,
    create_headdep_dicts
)

logger = logging.getLogger(None if __name__ == '__main__' else __name__)


stop_words = []


def get_relevant_head_ids(nafobj):
    '''
    Returns list of term ids that head potential mention
    :param nafobj: input nafobj
    :return: list of term ids (string)
    '''

    nominal_pos = ['noun','pron','name']
    mention_heads = []
    for term in nafobj.get_terms():
        pos_tag = term.get_pos()
        if pos_tag in nominal_pos:
            mention_heads.append(term.get_id())
        #check if possessive pronoun
        elif pos_tag == 'det' and 'VNW(bez' in term.get_morphofeat():
            mention_heads.append(term.get_id())

    return mention_heads


def get_mention_spans(nafobj):
    '''
    Function explores various layers of nafobj and retrieves all mentions
    possibly referring to an entity

    :param nafobj:  input nafobj
    :return:        dictionary of head term with as value constituent object
                    (head id, full head, modifiers, complete constituent)
    '''
    mention_heads = get_relevant_head_ids(nafobj)
    mention_constituents = get_constituents(nafobj, mention_heads)
    return mention_constituents


def get_string_of_term(nafobj, tid):

    my_term = nafobj.get_term(tid)
    termstring = ''
    latest_offset = '-1'

    for wid in my_term.get_span().get_span_ids():
        my_tok = nafobj.get_token(wid)
        # add space between tokens
        if len(termstring) > 0 and int(my_tok.get_offset) > latest_offset:
            termstring += ' '
        termstring += my_tok.get_text()
        latest_offset = int(my_tok.get_offset()) + int(my_tok.get_length())
    return termstring


def get_string_of_span(nafobj, span):

    mstring = ''
    latest_offset = -1
    for tid in span:
        my_term = nafobj.get_term(tid)
        for wid in my_term.get_span().get_span_ids():
            my_tok = nafobj.get_token(wid)
            #add space between tokens
            if len(mstring) > 0 and int(my_tok.get_offset()) > latest_offset:
                mstring += ' '
            mstring += my_tok.get_text()
            latest_offset = int(my_tok.get_offset()) + int(my_tok.get_length())
    return mstring


def get_pos_of_term(nafobj, tid):

    term = nafobj.get_term(tid)
    return term.get_pos()

def get_pos_of_span(nafobj, span):

    pos_seq = []
    for tid in span:
        tpos = get_pos_of_term(nafobj, tid)
        pos_seq.append(tpos)

    return pos_seq

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
        if lemma in ['haar','zijn','mijn','jouw','je']:
            mention.set_number('ev')
        elif lemma in ['ons','jullie','hun']:
            mention.set_number('mv')


def identify_and_set_gender(morphofeat, mention):

    if 'fem' in morphofeat:
        mention.set_number('fem')
    elif 'masc' in morphofeat:
        mention.set_number('masc')
    elif 'onz,' in morphofeat:
        mention.set_number('neut')

def set_is_relative_pronoun(morphofeat, mention):

    if 'betr,' in morphofeat:
        mention.set_relative_pronoun(True)
    if 'refl,' in morphofeat:
        mention.set_reflective_pronoun(True)



def analyze_nominal_information(nafobj, term_id, mention):

    myterm = nafobj.get_term(term_id)
    morphofeat = myterm.get_morphofeat()
    identify_and_set_person(morphofeat, mention)
    identify_and_set_gender(morphofeat, mention)
    identify_and_set_number(morphofeat, myterm, mention)
    set_is_relative_pronoun(morphofeat, mention)


def add_non_stopwords(nafobj, span, mention):
    '''
    Function that verifies which terms in span are not stopwords and adds these to non-stop-word list
    :param nafobj: input naf (for linguistic information)
    :param span: list of term ids
    :param mention: mention object
    :return:
    '''
    global stop_words
    non_stop_terms = []

    for tid in span:
        my_term = nafobj.get_term(tid)
        if not my_term.get_type() == 'closed' and not my_term.get_lemma().lower() in stop_words:
            non_stop_terms.append(tid)

    non_stop_span = convert_term_ids_to_offsets(nafobj, non_stop_terms)
    mention.set_no_stop_words(non_stop_span)

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


def get_sentence_number(nafobj, head):

    myterm = nafobj.get_term(head)
    tokid = myterm.get_span().get_span_ids()[0]
    mytoken = nafobj.get_token(tokid)
    sent_nr = int(mytoken.get_sent())

    return sent_nr




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

    span = constituentInfo.get_span()
    offset_ids_span = convert_term_ids_to_offsets(nafobj, span)
    mention = Cmention(mid, span=offset_ids_span, head_id=head_id)
    sentence_number = get_sentence_number(nafobj, head)
    mention.set_sentence_number(sentence_number)
    #add no stop words and main modifiers
    add_non_stopwords(nafobj, span, mention)
    add_main_modifiers(nafobj, span, mention)
    #mwe info
    full_head_tids = constituentInfo.get_multiword()
    full_head_span = convert_term_ids_to_offsets(nafobj, full_head_tids)
    mention.set_full_head(full_head_span)
    #modifers and appositives:
    relaxed_span = offset_ids_span
    for mod_in_tids in constituentInfo.get_modifiers():
        mod_span = convert_term_ids_to_offsets(nafobj, mod_in_tids)
        mention.add_modifier(mod_span)
        for mid in mod_span:
            if mid > head_id and mid in relaxed_span:
                relaxed_span.remove(mid)
    for app_in_tids in constituentInfo.get_appositives():
        app_span = convert_term_ids_to_offsets(nafobj, app_in_tids)
        mention.add_appositive(app_span)
        for mid in app_span:
            if mid > head_id and mid in relaxed_span:
                relaxed_span.remove(mid)
    mention.set_relaxed_span(relaxed_span)

    for pred_in_tids in constituentInfo.get_predicatives():
        pred_span = convert_term_ids_to_offsets(nafobj, pred_in_tids)
        mention.add_predicative(pred_span)

    #set sequence of pos FIXME: if not needed till end; remove
    #os_seq = get_pos_of_span(nafobj, span)
    #mention.set_pos_seq(pos_seq)
    #set pos of head
    if head != None:
        head_pos = get_pos_of_term(nafobj, head)
        mention.set_head_pos(head_pos)
        if head_pos in ['pron','noun','name']:
            analyze_nominal_information(nafobj, head, mention)

    begin_offset, end_offset = get_offsets_from_span(nafobj, span)
    mention.set_begin_offset(begin_offset)
    mention.set_end_offset(end_offset)

    return mention


def merge_two_mentions(mention1, mention2):
    '''
    Merge information from mention 1 into mention 2
    :param mention1:
    :param mention2:
    :return: updated mention
    '''
    # FIXME; The comments here do not correspond to the code and therefore the
    #        code may be horribly wrong.
    if mention1.head_id == mention2.head_id:
        if set(mention1.span) == set(mention2.span):
            # if mention1 does not have entity type, take the one from entity 2
            if mention2.get_entity_type() is None:
                mention2.set_entity_type(mention1.get_entity_type())
        else:
            # if mention2 has no entity type, it's span is syntax based
            # (rather than from the NERC module)
            if mention1.get_entity_type() is None:
                mention2.set_span(mention1.get_span())
    else:
        if mention1.get_entity_type() is None:
            mention2.set_head_id(mention1.get_head_id())
        else:
            mention2.set_entity_type(mention1.get_entity_type())

    return mention2


def merge_mentions(mentions, heads):
    '''
    Function that merges information from entity mentions
    :param mentions: dictionary mapping mention number to specific mention
    :param heads: dictionary mapping head id to mention number
    :return: list of mentions where identical spans are merged
    '''

    final_mentions = {}

    #TODO: create merge function and merge identical candidates

    for m, val in mentions.items():
        found = False
        for prevm, preval in final_mentions.items():
            if val.head_id == preval.head_id:
                updated_mention = merge_two_mentions(val, preval)
                final_mentions[prevm] = updated_mention
                found = True
            elif set(val.span) == set(preval.span):
               # print('same_set')
                updated_mention = merge_two_mentions(val, preval)
                final_mentions[prevm] = updated_mention
                found = True
        if not found:
            final_mentions[m] = val

    return final_mentions


def get_offsets_from_span(nafobj, span):
    '''
    Function that identifies begin and end offset for a span of terms
    :param nafobj: input naf
    :param span: list of term identifiers
    :return:
    '''

    offsets = []
    end_offsets = []
    for termid in span:
        offset = get_offset(nafobj, termid)
        length = get_term_length(nafobj, termid)
        offsets.append(offset)
        end_offsets.append(offset+length)

    begin_offset = 0
    end_offset = 0
    if len(offsets) > 0:
        begin_offset = sorted(offsets)[0]
        end_offset = sorted(end_offsets)[-1]

    return begin_offset, end_offset


def get_term_length(nafobj, term_id):
    '''
    Function that returns the length of a term
    :param nafobj: input naf
    :param term_id: id of term in question
    :return:
    '''

    my_term = nafobj.get_term(term_id)
    length = 0
    expected_offset = 0
    for wid in my_term.get_span().get_span_ids():
        my_token = nafobj.get_token(wid)
        offset = int(my_token.get_offset())
        token_length = int(my_token.get_length())
        length += token_length
        if expected_offset != 0 and expected_offset != offset:
            length += offset - expected_offset
        expected_offset = offset + token_length

    return length


def get_offset(nafobj, term_id):
    '''
    Function that returns beginning offset of term
    :param nafobj: input naf
    :param term_id: id of term in question
    :return:
    '''

    return min(
        int(nafobj.get_token(wid).get_offset())
        for wid in nafobj.get_term(term_id).get_span_ids()
    )


def get_mentions(nafobj):
    '''
    Function that creates mention objects based on mentions retrieved from NAF
    :param nafobj: input naf
    :return: list of Cmention objects
    '''

    initiate_stopword_list()
    create_headdep_dicts(nafobj)

    mention_spans = get_mention_spans(nafobj)
    mentions = {}
    heads = defaultdict(list)
    for head, constituentInfo in mention_spans.items():
        mid = 'm' + str(len(mentions))
        mention = create_mention(nafobj, constituentInfo, head, mid)
        mentions[mid] = mention
        heads[head].append(mid)

    entities = get_named_entities(nafobj)
    for entity, constituent in entities.items():
        mid = 'm' + str(len(mentions))
        mention = create_mention(nafobj, constituent, entity, mid)
        mention.set_entity_type(constituent.get_etype())
        mentions[mid] = mention
        heads[entity].append(mid)

    mentions = merge_mentions(mentions, heads)

    return mentions


def convert_term_ids_to_offsets(nafobj, seq):
    '''
    Convert a sequence of term IDs to a list of offsets
    :param nafobj:  input naf object
    :param seq:     sequence of term IDs
    :return:        a list of offsets
    '''

    return [
        get_offset(nafobj, tid)
        for tid in seq
    ]


def get_quotation_spans(nafobj):
    '''
    Function that goes through nafobj and identifies spans of quotations
    :param nafobj: input naf
    :return: list of quotation objects with span defined
    '''

    #FIXME investigate on development corpus what to do with embedded quotations; for now we'll assume a double quotation within a single quote is an error

    in_double_quotation = False
    in_single_quotation = False
    quotations = []
    for term in nafobj.get_terms():
        if term.get_lemma() in ['"','&amp;amp;amp;quot;']:
            if not in_double_quotation:
                in_double_quotation = True
                myQuote = CquotationNaf()
                myQuote.beginquote = term.get_id()
            else:
                in_double_quotation = False
                myQuote.endquote = term.get_id()
                quotations.append(myQuote)
            #break off single quotation if double quotation found during this
            if in_single_quotation:
                in_single_quotation = False
        elif in_double_quotation:
            myQuote.add_span_id(term.get_id())

        if term.get_lemma() == "'":
            if not in_single_quotation:
                in_single_quotation = True
                myQuoteSingle = CquotationNaf()
                myQuoteSingle.beginquote = term.get_id()
            else:
                in_single_quotation = False
                myQuoteSingle.endquote = term.get_id()
                quotations.append(myQuoteSingle)
        elif in_single_quotation:
            myQuoteSingle.add_span_id(term.get_id())

    return quotations


def create_set_of_tids_from_tidfunction(tidfunctionlist):

    tids = set()
    for tidfunc in tidfunctionlist:
        tids.add(tidfunc[0])

    return tids


def find_relevant_spans(deps, outside_ids):

    for dep in deps:
        if dep[0] in outside_ids and dep[1] in ['nucl/tag', 'dp/dp']:
            return dep[0]

    return None


def analyze_head_relations(nafobj, head_term, head2deps):

    dependents = head2deps.get(head_term)
    speaker = None
    addressee = None
    topic = None
    #FIXME: we want to check the preposition
    #FIXME: no dependents case does occur; check with bigger corpus
    if dependents is not None:
        for dep in dependents:
            if dep[1] == 'hd/su':
                speaker = get_constituent(dep[0])
            elif dep[1] == 'hd/obj2':
                term = nafobj.get_term(dep[0])
                if term.get_pos() == 'prep':
                    if dep[0] in head2deps:
                        for deprel in head2deps.get(dep[0]):
                            if deprel[1] == 'hd/obj1':
                                addressee = get_constituent(deprel[0])
                else:
                    addressee = get_constituent(dep[0])
            elif dep[1] in ['hd/mod']:
                term = nafobj.get_term(dep[0])
                if term.get_pos() == 'prep':

                    if dep[0] in head2deps:
                        #override addressee by complement if headed by preposition
                        for deprel in head2deps.get(dep[0]):
                            if deprel[1] == 'hd/obj1':
                                if term.get_lemma() == 'tegen':
                                    addressee = get_constituent(deprel[0])
                                elif term.get_lemma() == 'over':
                                    topic = get_constituent(deprel[0])


    return speaker, addressee, topic


def identify_direct_links_to_sip(nafobj, quotation):
    '''
    Function that identifies
    :param head2deps: dictionary linking head to dependents
    :param quotation: the quotation itself
    :return: boolean indicating whether source was found
    '''

    for tid in quotation.span:
        deps = head2deps.get(tid)
        if not deps is None:
            depids = create_set_of_tids_from_tidfunction(deps)
            #if one of deps falls outside of quote, it can be linked to the sip
            span_with_quotes = quotation.span + [quotation.beginquote] + [quotation.endquote]
            if len(depids.difference(set(span_with_quotes))) > 0:
                my_joint_set = depids.difference(set(span_with_quotes))
                head_term = find_relevant_spans(deps, my_joint_set)
                if not head_term is None:
                    speaker, addressee, topic = analyze_head_relations(nafobj, head_term, head2deps)
                    if not speaker is None:
                        speaker_in_offsets = convert_term_ids_to_offsets(nafobj, speaker)
                        quotation.source = speaker_in_offsets
                    if not addressee is None:
                        addressee_in_offsets = convert_term_ids_to_offsets(nafobj, addressee)
                        quotation.addressee = addressee_in_offsets
                    if not topic is None:
                        topic_in_offsets = convert_term_ids_to_offsets(nafobj, topic)
                        quotation.topic = topic_in_offsets


def check_if_quotation_contains_dependent(quotation):
    #FIXME: verify on larger set of development corpus whether this behavior is correct
    for tid in quotation.span:
        heads = dep2heads.get(tid)
        if not heads is None:
            headids = create_set_of_tids_from_tidfunction(heads)
            span_with_quotes = quotation.span + [quotation.beginquote] + [quotation.endquote]
            if len(headids.difference(set(span_with_quotes))) > 0:
                for headid in headids.difference(set(span_with_quotes)):
                    for headrel in heads:
                        if headrel[0] == headid:
                            if headrel[1] in ['cmp/body','hd/predc','hd/obj1','hd/vc','hd/su','hd/pc']:
                                return False
                            elif headrel[1] in ['crd/cnj']:
                                motherheadrels = dep2heads.get(headrel[0])
                                if motherheadrels is not None:
                                    for mhid in motherheadrels:
                                        if mhid[1] in ['cmp/body','hd/predc','hd/obj1','hd/vc','hd/su','hd/pc']:
                                            return False
                                  #  elif not mhid[1] in ['hd/app','tag/nucl','--/--','dp/dp','-- / --','nucl/sat']:
                                  #      print(tid, headids.difference(set(span_with_quotes)), 'has outside head')
                                  #      print(motherheadrels)
                            #FIXME: debugs need to be checked out on bigger corpus; set up development mode
                           # elif not headrel[1] in ['hd/app','tag/nucl','--/--','dp/dp','-- / --','nucl/sat']:
                           #     print(tid, headids.difference(set(span_with_quotes)), 'has outside head')
                           #     print(heads, quotation.span)
    return True


def get_sentences_of_quotation(nafobj, quotation):

    sentences = set()

    for tid in quotation.span:
        term = nafobj.get_term(tid)
        wid = term.get_span().get_span_ids()[0]
        token = nafobj.get_token(wid)
        sentence_nr = token.get_sent()
        #storing them as integers; they need to be sorted later
        sentences.add(int(sentence_nr))
    return sentences


def get_previous_and_next_sentence(sentences):

    ordered_sentences = sorted(sentences)
    if len(ordered_sentences) > 0:
        previous_sentence = ordered_sentences[0] - 1
        following_sentence = ordered_sentences[-1] + 1
    else:
        previous_sentence = 0
        following_sentence = 0

    return previous_sentence, following_sentence

def retrieve_sentence_preceding_sip(nafobj, terms):
    source_head = None
    for tid in terms:
        myterm = nafobj.get_term(tid)
        if myterm.get_lemma() == 'volgens':
            deps = head2deps.get(tid)
            if deps is not None:
                for dep in deps:
                    if dep[1] == 'hd/obj1':
                        source_head = dep[0]

    return source_head


def retrieve_quotation_following_sip(nafobj, terms):

    source_head = None
    for tid in terms:
        myterm = nafobj.get_term(tid)
        if myterm.get_lemma() == 'aldus':
            deps = head2deps.get(tid)
            if deps is not None:
                for dep in deps:
                    if dep[1] == 'hd/obj1':
                        source_head = dep[0]

    return source_head


def identify_addressee_or_topic_relations(nafobj, tid, quotation):

    #FIXME: language specific function
    heads = dep2heads.get(tid)
    if heads is not None:
        for headrel in heads:
            headterm = nafobj.get_term(headrel[0])
            if headterm.get_lemma() == 'tegen' or headrel[1] == 'hd/obj2':
                myconstituent = get_constituent(headterm.get_id())
                addressee = convert_term_ids_to_offsets(nafobj, myconstituent)
                quotation.addressee = addressee
                return True
            elif headterm.get_lemma() == 'over':
                myconstituent = get_constituent(headterm.get_id())
                topic = convert_term_ids_to_offsets(nafobj, myconstituent)
                quotation.topic = topic
                return True
    return False


def get_candidates_not_part_of_addressee_topic(candidate_names, quotation):

    remaining_candidates = []
    covered_tids = quotation.addressee + quotation.topic
    for tid in candidate_names:
        if not tid in covered_tids:
            myconstituent = get_constituent(tid)
            remaining_candidates.append(myconstituent)
            covered_tids += myconstituent
    return remaining_candidates


def extract_full_names_or_prons(nafobj, constituents):

    names = []
    for const in constituents:
        name = []
        for tid in const:
            term = nafobj.get_term(tid)
            if term.get_pos() == 'name':
                name.append(tid)
        if len(name) == 0 and len(const) != 0:
            names.append(const)
        else:
            names.append(name)
    return names


def get_closest(candidates):

    closest = []
    selected_cand = []
    for cand in candidates:
        candnums = create_ordered_number_span(cand)
        if len(closest) == 0 or candnums[-1] > closest[-1]:
            closest = candnums
            selected_cand = cand
    return selected_cand

def identify_primary_candidate(candidates):

    for cand in candidates:
        for tid in cand:
            if tid in dep2heads:
                for headrel in dep2heads:
                    if headrel[1] == 'hd/su':
                        return cand

    #if no highest ranking found, return closest candidate
    return get_closest(candidates)


def find_name_or_pronoun(nafobj, preceding_terms, quotation):

    #FIXME: not over paragraph borders; if nothing found, sentence after can also work
    candidate_names = []
    for tid in preceding_terms:
        term = nafobj.get_term(tid)
        if term.get_pos() == 'name' or term.get_pos() == 'pron':
            if not identify_addressee_or_topic_relations(nafobj, tid, quotation):
                candidate_names.append(term.get_id())

    #change make dictionary with head term to constituent
    if len(candidate_names) > 0:
        remaining_candidates = get_candidates_not_part_of_addressee_topic(candidate_names, quotation)
        if len(remaining_candidates) > 0:
            candidates = extract_full_names_or_prons(nafobj, remaining_candidates)
            if len(candidates) == 1:
                candidate_in_offsets = convert_term_ids_to_offsets(nafobj, candidates[0])
                quotation.source = candidate_in_offsets
            else:
                candidate = identify_primary_candidate(candidates)
                candidate_in_offsets = convert_term_ids_to_offsets(nafobj, candidate)
                quotation.source = candidate_in_offsets


def create_ordered_number_span(term_list):

    number_list = []
    for tid in term_list:
        if 't_' in tid:
            tnumber = int(tid.lstrip('t_'))
            number_list.append(tnumber)
        elif 't' in tid:
            tnumber = int(tid.lstrip('t'))
            number_list.append(tnumber)

    return sorted(number_list)


def get_preceding_terms_in_sentence(first_sentence, quotation_span):
    # FIXME; move to offset based ids earlier; then this hack is not necessary
    quotation_numbers = create_ordered_number_span(quotation_span)
    preceeding_terms = []
    if len(quotation_numbers) > 0:
        for tid in first_sentence:
            if 't_' in tid:
                tnumber = int(tid.lstrip('t_'))
                if tnumber < quotation_numbers[0]:
                    preceeding_terms.append(tid)
            elif 't' in tid:
                tnumber = int(tid.lstrip('t'))
                if tnumber < quotation_numbers[0]:
                    preceeding_terms.append(tid)
    return preceeding_terms


def get_following_terms_in_sentence(last_sentence, quotation_span):

    # FIXME; move to offset based ids earlier; then this hack is not necessary
    quotation_numbers = create_ordered_number_span(quotation_span)
    following_terms = []
    for tid in last_sentence:
        if 't_' in tid:
            tnumber = int(tid.lstrip('t_'))
            if tnumber > quotation_numbers[0]:
                following_terms.append(tid)
        elif 't' in tid:
            tnumber = int(tid.lstrip('t'))
            if tnumber > quotation_numbers[0]:
                following_terms.append(tid)
    return following_terms


def identify_source_introducing_constructions(nafobj, quotation, sentence_to_term):
    '''
    Function that identifies structures that introduce sources of direct quotes
    :param nafobj: the input nafobj
    :param quotation: the quotation
    :return: None
    '''

    sentences = get_sentences_of_quotation(nafobj, quotation)
    prev_sent, follow_sent = get_previous_and_next_sentence(sentences)
    #FIXME: find out using development data whether preceding and following sentence should be taken into account or not
    #preceding_terms = sentence_to_term.get(str(prev_sent)) + sentence_to_term.get(str(prev_sent + 1))

    #start with 'aldus' construction; this is more robust
    following_sentence = sentence_to_term.get(str(follow_sent - 1))
    source_head = None
    if following_sentence is not None:
        following_terms = get_following_terms_in_sentence(following_sentence,quotation.span)
        source_head = retrieve_quotation_following_sip(nafobj,following_terms)

    if source_head is None:
        preceding_terms = get_preceding_terms_in_sentence(sentence_to_term.get(str(prev_sent + 1)),quotation.span)
        source_head = retrieve_sentence_preceding_sip(nafobj, preceding_terms)

    if source_head is not None:
        source_constituent = get_constituent(source_head)
        source_in_offsets = convert_term_ids_to_offsets(nafobj, source_constituent)
        quotation.source = source_in_offsets
    else:
        find_name_or_pronoun(nafobj, preceding_terms, quotation)
    #3. check previous sentence for name or pronoun


def get_sentence_to_terms(nafobj):

    token2terms = {}
    for term in nafobj.get_terms():
        tokens = term.get_span().get_span_ids()
        for tok in tokens:
            token2terms[tok] = term.get_id()

    sentence2terms = defaultdict(list)
    for token in nafobj.get_tokens():
        sent_nr = token.get_sent()
        term_id = token2terms.get(token.get_id())
        sentence2terms[sent_nr].append(term_id)

    return sentence2terms


def get_reduced_list_of_quotations(toremove, found_quotations):

    reduced_quotations = []
    for quote in found_quotations:
        wrong = False
        for wrong_quote in toremove:
            if set(quote.span) == set(wrong_quote.span):
                wrong = True
        if not wrong:
            reduced_quotations.append(quote)
    return reduced_quotations


def identify_direct_quotations(nafobj, mentions):
    '''
    Function that identifies direct quotations in naf
    :param nafobj: input naf object
    :return:
    '''

    nafquotations = get_quotation_spans(nafobj)
    # create_headdep_dicts(nafobj)
    toremove = []
    for quotation in nafquotations:
        identify_direct_links_to_sip(nafobj, quotation)
        if len(quotation.source) == 0:
            #this can lead to indication of quotation being attribution rather than quotation
            if check_if_quotation_contains_dependent(quotation):
                sentence_to_terms = get_sentence_to_terms(nafobj)
                identify_source_introducing_constructions(nafobj, quotation, sentence_to_terms)
            else:
                toremove.append(quotation)

    finalnafquotations = get_reduced_list_of_quotations(toremove, nafquotations)
    quotations = []
    for qid, nafquotation in enumerate(finalnafquotations):
        myquote = create_coref_quotation_from_quotation_naf(nafobj, nafquotation, mentions, qid)
        quotations.append(myquote)

    return quotations


def link_span_ids_to_mentions(span, mentions):
    '''
    Function that takes span as input and finds out whether this corresponds to a mention candidate and, if so, which one
    :param span: list of span ids
    :param mentions: object containing all candidate mentions
    :return:
    '''

    for key, mention in mentions.items():
        if set(span) == set(mention.span):
            return key

    for key, mention in mentions.items():
        if set(span).issubset(set(mention.span)) or set(span).issuperset(mention.span):
            return key

#    import traceback; print(traceback.extract_stack(limit=2)[-1][2] + " - span: " + str(span))


def create_coref_quotation_from_quotation_naf(nafobj, nafquotation, mentions, quote_id):
    '''
    Function that turns naf quotation object into quotation object to be passed on to multisieve
    :param nafobj: input naf
    :param nafquotation: quotation object with naf specific information
    :param quote_id: identifier for quotation
    :return:
    '''

    myQuote = Cquotation(quote_id)

    quotespan = convert_term_ids_to_offsets(nafobj, nafquotation.span)
    myQuote.set_span(quotespan)

    quotestring = get_string_of_span(nafobj, nafquotation.span)
    myQuote.set_string(quotestring)

    beginoffset, endoffset = get_offsets_from_span(nafobj, nafquotation.span)
    myQuote.set_begin_offset(beginoffset)
    myQuote.set_end_offset(endoffset)

    if len(nafquotation.source) > 0:
        source_mention_id = link_span_ids_to_mentions(nafquotation.source, mentions)
        myQuote.set_source(source_mention_id)
    if len(nafquotation.addressee) > 0:
        addressee_mention_id = link_span_ids_to_mentions(nafquotation.addressee, mentions)
        myQuote.set_addressee(addressee_mention_id)
    if len(nafquotation.topic) > 0:
        topic_mention_id = link_span_ids_to_mentions(nafquotation.topic, mentions)
        myQuote.set_topic(topic_mention_id)

    return myQuote


def initiate_stopword_list(lang='nl'):

    global stop_words
    resources = os.path.abspath(os.path.join(os.path.dirname(__file__), "resources"))
    
    stopfile = open(os.path.join(resources, lang, 'stop_words.txt'),'r')
    for line in stopfile:
        stop_words.append(line.rstrip())

    stopfile.close()

def initiate_id2string_dicts(nafobj):

    id2string = {}
    id2lemma = {}

    for term in nafobj.get_terms():
        identifier = get_offset(nafobj, term.get_id())
        lemma = term.get_lemma()
        id2lemma[identifier] = lemma

    for token in nafobj.get_tokens():
        identifier = int(token.get_offset())
        surface_string = token.get_text()
        id2string[identifier] = surface_string

    return id2string, id2lemma

