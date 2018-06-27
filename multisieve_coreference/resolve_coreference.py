import sys
import logging
from collections import defaultdict

from KafNafParserPy import KafNafParser

from . import constants as c
from .dump import add_coreference_to_naf
from .naf_info import (
    get_mentions,
    identify_direct_quotations,
    initiate_id2string_dicts
)


logger = logging.getLogger(None if __name__ == '__main__' else __name__)


#global values mapping identifiers to string and lemma respectively
id2string = {}
id2lemma = {}


def get_string_from_ids(id_span):

    global id2string

    surface_string = ''

    for mid in id_span:
        token_string = id2string.get(mid)
        surface_string += token_string + ' '

    return surface_string.rstrip()


def match_some_span(mentions, coref_classes, get_span):
    '''
    Function that places entities with full string match in the same coreference group
    :param mentions: dictionary of all available mention objects (key is
                     mention id)
    :param coref_classes: dictionary of coreference classes (key is class id)
    :param get_span: function that returns a span given a `Cmention` object.
    '''
    found_entities = {}

    #FIXME: verify (when evaluating) whether prohibited needs to be taken into account here
    #FIXME 2: now only surface strings, we may want to look at lemma matches as well
    for mid, mention in mentions.items():
        if mention.head_pos in ['name', 'noun']:
            mention_string = get_string_from_ids(get_span(mention))
            if mention_string in found_entities:
                coref_id = found_entities.get(mention_string)
                if coref_id not in mention.in_coref_class:
                    mention.in_coref_class.append(coref_id)
                    coref_classes[coref_id].add(mention.id)
            else:
                #coref classes will usually have a length 1; if not, it doesn't matter which one is picked
                if len(mention.in_coref_class) > 0:
                    coref_nr = mention.in_coref_class[0]
                else:
                    coref_nr = len(coref_classes)
                    mention.in_coref_class.append(coref_nr)
                coref_classes[coref_nr].add(mention.id)
                found_entities[mention_string] = coref_nr


def match_full_name_overlap(mentions, coref_classes):
    '''
    Function that places entities with full string match in the same
    coreference group
    :param mentions: dictionary of all available mention objects (key is
                     mention id)
    :param coref_classes: dictionary of coreference classes (key is class id)
    '''
    match_some_span(mentions, coref_classes, lambda m: m.span)


def match_relaxed_string(mentions, coref_classes):
    '''
    Function that matches mentions which have the same relaxed head
    :param mentions: dictionary of all available mention objects (key is
                     mention id)
    :param coref_classes: dictionary of coreference classes (key is class id)
    '''
    match_some_span(mentions, coref_classes, lambda m: m.relaxed_span)


def update_coref_class(coref_class, current_mention, coref_mention):
    '''
    Function that creates new input for coref class when coreference identified
    :param coref_class: coref_class dictionary
    :param current_mention: mention in quotation
    :param coref_mention: corefering mention
    :return:
    '''

    if len(coref_mention) > 0:

        coref_class_id = len(coref_class)
        coref_class[coref_class_id].add(current_mention.id)
        coref_class[coref_class_id].add(coref_mention)

def included_in_direct_speech(quotations, mention, coref_class):
    '''
    Function that verifies whether mention is included in some quotation
    :param quotations: list of quotations
    :param mention: a specific mention
    :return:
    '''
    mention_span_set = set(mention.span)
    for quote in quotations:
        if mention_span_set.issubset(set(quote.span)):
            #FIXME check if needed
            mention.in_quotation = True
            source = quote.source
            addressee = quote.addressee
            topic = quote.topic
            if mention.head_pos == 'pron':
                if mention.person == '1':
                    if source is not None:
                        update_coref_class(coref_class, mention, source)
                    if topic is not None:
                        mention.coreference_prohibited.append(topic)
                    if addressee is not None:
                        mention.coreference_prohibited.append(addressee)
                elif mention.person == '2':
                    if source is not None:
                        mention.coreference_prohibited.append(source)
                    if topic is not None:
                        mention.coreference_prohibited.append(topic)
                    if addressee is not None:
                        update_coref_class(coref_class, mention, addressee)
                elif mention.person == '3':
                    if source is not None:
                        mention.coreference_prohibited.append(source)
                    if topic is not None:
                        update_coref_class(coref_class, mention, topic)
                    if addressee is not None:
                        mention.coreference_prohibited.append(addressee)
            elif source is not None:
                    mention.coreference_prohibited.append(source)
                #TODO once vocative check installed; also prohibit linking names to speaker




def direct_speech_interpretation(quotations, mentions):
    '''
    Function that applies the first sieve; assigning coreference or prohibited coreference
    based on direct speech
    :param quotations: list of quotation objects
    :param mentions: list of mention objects
    :return: None
    '''
    coref_classes = defaultdict(set)
    for mid, mention in mentions.items():
        included_in_direct_speech(quotations, mention, coref_classes)

    return coref_classes


def update_mentions(mentions, coref_classes):
    '''
    Function that indicates in mention representations to which coref_class they have been assigned (if any)
    :param mentions:
    :param coref_classes:
    :return:
    '''
    for k, corefs in coref_classes.items():
        if corefs is not None:
            for coref in corefs:
                mention = mentions.get(coref)
                #we don't need to mark it more than once
                if not k in mention.in_coref_class:
                    mention.in_coref_class.append(k)

def merge_merge_list(merge_lists):

    #FIXME: check this function for artificial context (i.e. create unit test)
    new_merge_list = []
    for to_merge in merge_lists:
        merge_with_previous = False
        for mid in to_merge:
            for i, nml in enumerate(new_merge_list):
                if mid in nml:
                    merge_with_previous = True
                    updated_nml = set(nml) | set(to_merge)
                    new_merge_list[i] = updated_nml
        if not merge_with_previous:
            new_merge_list.append(set(to_merge))
    return new_merge_list


def clean_up_coref_classes(coref_classes, mentions):

    to_merge = []
    for mid, mention in mentions.items():
        if len(mention.in_coref_class) > 1:
            to_merge.append(mention.in_coref_class)

    grouped_merge_list = merge_merge_list(to_merge)

    for merges in grouped_merge_list:
        merges = sorted(merges)
        overall_id = merges[0]
        for cid in merges[1:]:
            coref_classes[overall_id] |= coref_classes.pop(cid)

        # reset mention coreference class to selected id
        for mention_id in coref_classes[overall_id]:
            mentions[mention_id].in_coref_class = [overall_id]


def identify_span_matching_mention(span, mid, mentions):
    """
    Find the mentions different from `mid` that have the same span as `span`.

    :param span:        span to match mention spans against
    :param mid:         ID of the mention that should be ignored
    :param mentions:    {ID: mention} dictionary of all mentions to consider
    :return:            list of IDs of mentions that have `span` as their span
    """

    matching_mentions = []
    for ment_id, mention in mentions.items():
        if not ment_id == mid:
            if set(mention.span) == set(span):
                matching_mentions.append(ment_id)

    return matching_mentions


def update_matching_mentions(mentions, matches, mention1, coref_classes):
    '''
    Function that updates mentions and coref_classes objected based on identified matches
    :param mentions:
    :param mention1:
    :param match:
    :param coref_classes:
    :return:
    '''
    coref_id = None
    if len(mention1.in_coref_class) > 0:
        for c_class in mention1.in_coref_class:
            if coref_classes[c_class] is not None:
                coref_id = c_class
    else:
        for matching_ment in matches:
            myMention = mentions.get(matching_ment)
            if len(myMention.in_coref_class) > 0:
                for c_coref in myMention.in_coref_class:
                    if coref_classes.get(c_coref) is not None:
                        coref_id = c_coref
    if coref_id is None:
        coref_id = len(coref_classes)
    if mention1.id not in coref_classes[coref_id]:
        coref_classes[coref_id].add(mention1.id)
        if coref_id not in mention1.in_coref_class:
            mention1.in_coref_class.append(coref_id)
    for matching in matches:
        if matching not in coref_classes[coref_id]:
            coref_classes[coref_id].add(matching)
            matchingMention = mentions.get(matching)
            if coref_id not in matchingMention.in_coref_class:
                matchingMention.in_coref_class.append(coref_id)


def identify_some_structures(mentions, coref_classes, get_structures):
    """
    Assigns coreference for some structures in place

    :param mentions:       dictionary of all available mention objects (key is
                           mention id)
    :param coref_classes:  dictionary of coreference classes (key is class id)
    :param get_structures: function that returns a list of spans given a
                           `Cmention` object.
    """
    for mid, mention in mentions.items():
        structures = get_structures(mention)
        for structure in structures:
            matching_mentions = identify_span_matching_mention(
                structure,
                mid,
                mentions
            )
            if len(matching_mentions) > 0:
                update_matching_mentions(
                    mentions,
                    matching_mentions,
                    mention,
                    coref_classes
                )


def identify_appositive_structures(mentions, coref_classes):
    '''
    Assigns coreference for appositive structures in place

    :param mentions:       dictionary of all available mention objects (key is
                           mention id)
    :param coref_classes:  dictionary of coreference classes (key is class id)
    '''
    identify_some_structures(mentions, coref_classes, lambda m: m.appositives)


def identify_predicative_structures(mentions, coref_classes):
    '''
    Assigns coreference for predicative structures in place
    :param mentions:       dictionary of all available mention objects (key is
                           mention id)
    :param coref_classes:  dictionary of coreference classes (key is class id)
    '''
    identify_some_structures(mentions, coref_classes, lambda m: m.predicatives)


def get_closest_match_relative_pronoun(mentions, matching, mention_index):

    candidates = {}
    for mid in matching:
        mention = mentions.get(mid)
        offset = mention.head_offset
        candidates[mention] = offset
    antecedent = identify_closest_candidate(mention_index, candidates)
    return antecedent



def resolve_relative_pronoun_structures(mentions, coref_classes):
    '''
    Identifies relative pronouns and assigns them to the class of the noun they're modifying
    :param mentions: dictionary of mentions
    :param coref_classes: dictionary of coreference class with all coreferring mentions as value
    :return: None (mentions and coref_classes are updated)
    '''
    for m, mention in mentions.items():
        if mention.is_relative_pronoun:
            matching = []
            for om, othermention in mentions.items():
                if not om == m and mention.head_offset not in othermention.span:
                    for mod in othermention.modifiers:
                        if mention.head_offset in mod:
                            matching.append(om)
            if len(matching) == 1:
                update_matching_mentions(mentions, matching, mention, coref_classes)
            elif len(matching) > 1:
                mention_index = mention.head_offset
                my_match = get_closest_match_relative_pronoun(mentions, matching, mention_index)
                update_matching_mentions(mentions, [my_match.id], mention, coref_classes)

def resolve_reflective_pronoun_structures(mentions, coref_classes):
    '''
    Identifies mention that is correct coreference for relfectives
    :param mentions:
    :param coref_classes:
    :return:
    '''
    for m, mention in mentions.items():
        if mention.is_reflective_pronoun:
            matching = []
            sent_nr = mention.sentence_number
            for om, othermention in mentions.items():
                if othermention.sentence_number == sent_nr:
                    if not om == m and mention.head_offset not in othermention.span:
                        if int(othermention.head_offset) < mention.head_offset:
                            matching.append(om)
            if len(matching) == 1:
                update_matching_mentions(mentions, matching, mention, coref_classes)
            elif len(matching) > 1:
                mention_index = mention.head_offset
                my_match = get_closest_match_relative_pronoun(mentions, matching, mention_index)
                update_matching_mentions(mentions, [my_match.id], mention, coref_classes)




def identify_acronyms_or_alternative_names(mentions, coref_classes):
    '''
    Identifies structures that add alternative name
    :param mentions: dictionary of mentions
    :param coref_classes: dictionary of coreference class with all coreferring mentions as value
    :return: None (mentions and coref_classes are updated)
    '''
    #FIXME input specific
    for m, mention in mentions.items():
        if mention.entity_type in ['PER', 'ORG', 'LOC', 'MISC'] and len(mention.modifiers) > 0:
            final_matches = []
            for mod in mention.modifiers:
                matching_mentions = identify_span_matching_mention(mod, m, mentions)
                for matchid in matching_mentions:
                    mymatch = mentions.get(matchid)
                    if mymatch.entity_type in ['PER', 'ORG', 'LOC', 'MISC']:
                        final_matches.append(matchid)
            if len(final_matches) > 0:
                update_matching_mentions(mentions, final_matches, mention, coref_classes)


def get_sentence_mentions(mentions):

    sentenceMentions = defaultdict(list)

    for mid, mention in mentions.items():
        snr = mention.sentence_number
        sentenceMentions[snr].append(mid)

    return sentenceMentions



def add_coref_prohibitions(mentions, coref_classes):

    sentenceMentions = get_sentence_mentions(mentions)
    for snr, mids in sentenceMentions.items():
        for mid in mids:
            mention = mentions.get(mid)
            corefs = []
            for c_class in mention.in_coref_class:
                corefs += coref_classes.get(c_class)
            for same_sent_mid in mids:
                if not same_sent_mid == mid and not same_sent_mid in corefs:
                    mention.coreference_prohibited.append(same_sent_mid)




def apply_precise_constructs(mentions, coref_classes):
    '''
    Function that moderates the precise constructs (calling one after the other
    :param mentions: dictionary storing mentions
    :param coref_classes: dictionary storing coref_classes so far
    :return: None (mentions and coref_classes are updated)
    '''
    identify_appositive_structures(mentions, coref_classes)
    identify_predicative_structures(mentions, coref_classes)
    resolve_relative_pronoun_structures(mentions, coref_classes)
    identify_acronyms_or_alternative_names(mentions, coref_classes)
    resolve_reflective_pronoun_structures(mentions, coref_classes)
    #f. Demonym Israel, Israeli (later)


def find_strict_head_antecedents(mention, mentions, sieve):
    '''
    Function that looks at which other mentions might be antecedent for the current mention
    :param mention: current mention
    :param mentions: dictionary of all mentions
    :return: list of antecedent ids
    '''
    head_string = id2string.get(mention.head_offset)
    non_stop_words = get_string_from_ids(mention.no_stop_words)
    main_mods = get_string_from_ids(mention.main_modifiers)
    antecedents = []
    for mid, comp_mention in mentions.items():
        #offset must be smaller to be antecedent and not i-to-i
        if comp_mention.head_offset < mention.head_offset and \
           not mention.head_offset <= comp_mention.end_offset:
            if head_string == id2string.get(comp_mention.head_offset):
                match = True
                full_span = get_string_from_ids(comp_mention.span)
                if sieve in ['5','7']:
                    for non_stop_word in non_stop_words:
                        if not non_stop_word in full_span:
                            match = False
                if sieve in ['5','6']:
                    for mmod in main_mods:
                        if not mmod in full_span:
                            match = False
                if match:
                    antecedents.append(mid)

    return antecedents


def apply_strict_head_match(mentions, coref_classes, sieve='5'):

    #FIXME: parser specific check for pronoun
    for mention in mentions.values():
        if not mention.head_pos == 'pron':
            antecedents = find_strict_head_antecedents(mention, mentions, sieve)
            if len(antecedents) > 0:
                update_matching_mentions(mentions, antecedents, mention, coref_classes)


def only_identical_numbers(span1, span2):

    word_list1 = get_string_from_ids(span1)
    word_list2 = get_string_from_ids(span2)

    for word in word_list1:
        if word.isdigit() and not word in word_list2:
            return False

    return True


def contains_number(span):

    for word in get_string_from_ids(span):
        if word.isdigit():
            return True

    return False


def find_head_match_coreferents(mention, mentions):
    '''
    Function that looks at which mentions might be antecedent for the current mention
    :param mention: current mention
    :param mentions: dictionary of all mentions
    :return: list of mention coreferents
    '''

    boffset = mention.begin_offset
    eoffset = mention.end_offset
    full_head_string = get_string_from_ids(mention.full_head)
    contains_numbers = contains_number(mention.span)

    coreferents = []

    for mid, comp_mention in mentions.items():
        if mid != mention.id and comp_mention.entity_type in ['PER', 'ORG', 'LOC']:
            #mention may not be included in other mention
            if not comp_mention.begin_offset <= boffset and comp_mention.end_offset >= eoffset:
                match = True
                comp_string = get_string_from_ids(comp_mention.full_head)
                for word in full_head_string.split():
                    if not word in comp_string:
                        match = False
                if contains_numbers and contains_number(comp_mention.span):
                    if not only_identical_numbers(mention.span, comp_mention.span):
                        match = False
                if match:
                    coreferents.append(mid)

    return coreferents



def apply_proper_head_word_match(mentions, coref_classes):

    #FIXME: tool specific output for entity type
    for mention in mentions.values():
        if mention.entity_type in ['PER', 'ORG', 'LOC', 'MISC']:
            coreferents = find_head_match_coreferents(mention, mentions)
            if len(coreferents) > 0:
                update_matching_mentions(mentions, coreferents, mention, coref_classes)



def find_relaxed_head_antecedents(mention, mentions):
    '''
    Function that identifies antecedents for which relaxed head match applies
    :param mention:
    :param mentions:
    :return:
    '''

    boffset = mention.begin_offset
    full_head_string = get_string_from_ids(mention.full_head)
    non_stop_words = get_string_from_ids(mention.no_stop_words)
    antecedents = []

    for mid, comp_mention in mentions.items():
        #we want only antecedents
        if comp_mention.end_offset < boffset:
            if comp_mention.entity_type == mention.entity_type:
                match = True
                full_comp_head = get_string_from_ids(comp_mention.full_head)
                for word in full_head_string.split():
                    if not word in full_comp_head:
                        match = False
                full_span = get_string_from_ids(comp_mention.span)
                for non_stop_word in non_stop_words:
                    if not non_stop_word in full_span:
                        match = False
                if match:
                    antecedents.append(mid)

    return antecedents


def apply_relaxed_head_match(mentions, coref_classes):

    for mention in mentions.values():
        if mention.entity_type in ['PER', 'ORG', 'LOC', 'MISC']:
            antecedents = find_relaxed_head_antecedents(mention, mentions)
            if len(antecedents) > 0:
                update_matching_mentions(mentions, antecedents, mention, coref_classes)


def is_compatible(string1, string2):
    '''
    Generic function to check if values are not incompatible
    :param string1: first string
    :param string2: second string
    :return: boolean
    '''
    #if either is underspecified, they are not incompatible
    if string1 is None or string2 is None:
        return True
    if len(string1) == 0 or len(string2) == 0:
        return True
    if string1 == string2:
        return True

    return False


def check_compatibility(mention1, mention2):

    if not is_compatible(mention1.number, mention2.number):
        return False
    if not is_compatible(mention1.gender, mention2.gender):
        return False
    #speaker/addressee 1/2 person was taken care of earlier on
    if not is_compatible(mention1.person, mention2.person):
        return False
    if not is_compatible(mention1.entity_type, mention2.entity_type):
        return False

    return True


def get_candidates_and_distance(mention, mentions):

    candidates = {}
    sent_nr = mention.sentence_number
    for mid, comp_mention in mentions.items():
        if mention.head_offset > comp_mention.head_offset:
            csnr = comp_mention.sentence_number
            #only consider up to 3 preceding sentences
            if csnr <= sent_nr <= csnr + 3:
                #check if not prohibited
                if not mid in mention.coreference_prohibited:
                    if check_compatibility(mention, comp_mention):
                        candidates[mid] = comp_mention.head_offset

    return candidates


def identify_closest_candidate(mention_index, candidates):


    distance = 1000000
    antecedent = None
    for candidate, head_index in candidates.items():
        candidate_distance = mention_index - head_index
        if candidate_distance < distance:
            distance = candidate_distance
            antecedent = candidate
    return antecedent


def identify_antecedent(mention, mentions):

    candidates = get_candidates_and_distance(mention, mentions)
    mention_index = mention.head_offset
    antecedent = identify_closest_candidate(mention_index, candidates)

    return antecedent


def resolve_pronoun_coreference(mentions, coref_classes):

    for mention in mentions.values():
        #we only deal with unresolved pronouns here
        if mention.head_pos == 'pron' and len(mention.in_coref_class) == 0:
            antecedent = identify_antecedent(mention, mentions)
            if antecedent is not None:
                update_matching_mentions(mentions, [antecedent], mention, coref_classes)



def initialize_global_dictionaries(nafobj):

    global id2string, id2lemma

    id2string, id2lemma = initiate_id2string_dicts(nafobj)



def resolve_coreference(nafin):

    initialize_global_dictionaries(nafin)
    mentions = get_mentions(nafin)
    quotations = identify_direct_quotations(nafin, mentions)

    if logger.getEffectiveLevel() <= logging.DEBUG:
        from .util import view_mentions
        logger.debug(
            "Mentions just before S1: {}".format(
                view_mentions(nafin, mentions)
            )
        )

    logger.info("Sieve 1: Speaker Identification")
    coref_classes = direct_speech_interpretation(quotations, mentions)
    update_mentions(mentions, coref_classes)

    if logger.getEffectiveLevel() <= logging.DEBUG:
        from .util import view_coref_classes
        logger.debug(
            "Coreference classes: {}".format(
                view_coref_classes(nafin, coref_classes, mentions)
            )
        )

    logger.info("Sieve 2: String Match")
    match_full_name_overlap(mentions, coref_classes)
    clean_up_coref_classes(coref_classes, mentions)
    update_mentions(mentions, coref_classes)

    if logger.getEffectiveLevel() <= logging.DEBUG:
        logger.debug(
            "Coreference classes: {}".format(
                view_coref_classes(nafin, coref_classes, mentions)
            )
        )

    logger.info("Sieve 3: Relaxed String Match")
    match_relaxed_string(mentions, coref_classes)
    clean_up_coref_classes(coref_classes, mentions)
    update_mentions(mentions, coref_classes)

    if logger.getEffectiveLevel() <= logging.DEBUG:
        logger.debug(
            "Coreference classes: {}".format(
                view_coref_classes(nafin, coref_classes, mentions)
            )
        )

    logger.info("Sieve 4: Precise constructs")
    apply_precise_constructs(mentions, coref_classes)
    clean_up_coref_classes(coref_classes, mentions)
    update_mentions(mentions, coref_classes)

    if logger.getEffectiveLevel() <= logging.DEBUG:
        logger.debug(
            "Coreference classes: {}".format(
                view_coref_classes(nafin, coref_classes, mentions)
            )
        )

    logger.info("Sieve 5-7: Strict Head Match")
    apply_strict_head_match(mentions, coref_classes)
    clean_up_coref_classes(coref_classes, mentions)
    update_mentions(mentions, coref_classes)

    if logger.getEffectiveLevel() <= logging.DEBUG:
        logger.debug(
            "Coreference classes: {}".format(
                view_coref_classes(nafin, coref_classes, mentions)
            )
        )

    logger.info("Sieve 8: Proper Head Word Match")
    apply_proper_head_word_match(mentions, coref_classes)
    clean_up_coref_classes(coref_classes, mentions)
    update_mentions(mentions, coref_classes)

    if logger.getEffectiveLevel() <= logging.DEBUG:
        logger.debug(
            "Coreference classes: {}".format(
                view_coref_classes(nafin, coref_classes, mentions)
            )
        )

    logger.info("Sieve 9: Relaxed Head Match")
    apply_relaxed_head_match(mentions, coref_classes)
    clean_up_coref_classes(coref_classes, mentions)
    update_mentions(mentions, coref_classes)

    if logger.getEffectiveLevel() <= logging.DEBUG:
        logger.debug(
            "Coreference classes: {}".format(
                view_coref_classes(nafin, coref_classes, mentions)
            )
        )

    logger.info("Sieve 10")

    logger.info("Add coreferences prohibitions")
    add_coref_prohibitions(mentions, coref_classes)

    if logger.getEffectiveLevel() <= logging.DEBUG:
        logger.debug(
            "Coreference classes: {}".format(
                view_coref_classes(nafin, coref_classes, mentions)
            )
        )

    logger.info("Resolve relative pronoun coreferences")
    resolve_pronoun_coreference(mentions, coref_classes)

    if logger.getEffectiveLevel() <= logging.DEBUG:
        logger.debug(
            "Coreference classes: {}".format(
                view_coref_classes(nafin, coref_classes, mentions)
            )
        )

    clean_up_coref_classes(coref_classes, mentions)
    update_mentions(mentions, coref_classes)

    if logger.getEffectiveLevel() <= logging.DEBUG:
        logger.debug(
            "Coreference classes: {}".format(
                view_coref_classes(nafin, coref_classes, mentions)
            )
        )

    return coref_classes, mentions


def process_coreference(
        nafin,
        include_singletons=c.INCLUDE_SINGLETONS_IN_OUTPUT):
    """
    Process coreferences and add to the given NAF.
    Note that coreferences are added in place, and the NAF is returned for convenience
    """
    coref_classes, mentions = resolve_coreference(nafin)
    if not include_singletons:
        logger.info("Removing singleton coreference classes")
        remove_singleton_coreference_classes(coref_classes)

    logger.info("Adding coreference information to NAF...")
    add_coreference_to_naf(nafin, coref_classes, mentions)
    return nafin


def remove_singleton_coreference_classes(coref_classes):
    singletons = set()
    for cID, mention_ids in coref_classes.items():
        if len(mention_ids) < 2:
            singletons.add(cID)

    for cID in singletons:
        del coref_classes[cID]


def main(argv=None):
    # args and options left for later
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-l', '--level', help="Logging level",
                        default='WARNING')
    parser.add_argument(
        '-s',
        '--include_singletons',
        help="Whether to include singletons in the output",
        action='store_true',
        dest='include_singletons'
    )
    cmdl_args = vars(parser.parse_args(argv))
    logging.basicConfig(level=cmdl_args.pop('level'))

    logger.info("Reading...")
    nafin = KafNafParser(sys.stdin)
    logger.info("Processing...")
    nafin = process_coreference(nafin, **cmdl_args)
    logger.info("Writing...")
    nafin.dump()


if __name__ == '__main__':
    main()
