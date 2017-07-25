import sys
from KafNafParserPy import *
from collections import defaultdict
from .naf_info import get_mentions, add_coreference_to_naf, identify_direct_quotations, initiate_id2string_dicts


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


def match_full_name_overlap(mentions, coref_classes):
    '''
    Function that places entities with full string match in the same coreference group
    :param mentions: dictionary of mention objects (key is mention id)
    :return:
    '''
    found_entities = {}

    #FIXME: verify (when evaluating) whether prohibited needs to be taken into account here
    #FIXME 2: now only surface strings, we may want to look at lemma matches as well
    for mid, mention in mentions.items():
        if mention.get_head_pos() in ['name', 'noun']:
            mention_string = get_string_from_ids(mention.get_span())
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


def match_relaxed_string(mentions, coref_classes):
    '''
    Function that matches mentions which have the same relaxed head
    :param mentions: all available mentions
    :param coref_classes: coreference classes
    :return:
    '''
    found_relaxed_strings = {}
    for mid, mention in mentions.items():
        if mention.get_head_pos() in ['name','noun']:
            relaxed_string = get_string_from_ids(mention.get_relaxed_span())
            if relaxed_string in found_relaxed_strings:
                coref_id = found_relaxed_strings.get(relaxed_string)
                if coref_id not in mention.in_coref_class:
                    mention.in_coref_class.append(coref_id)
                    coref_classes[coref_id].add(mention.id)
            else:
                if len(mention.in_coref_class) > 0:
                    coref_nr = mention.in_coref_class[0]
                else:
                    coref_nr = len(coref_classes)
                    mention.in_coref_class.append(coref_nr)
                coref_classes[coref_nr].add(mention.id)
                found_relaxed_strings[relaxed_string] = coref_nr


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
            source = quote.get_source()
            addressee = quote.get_addressee()
            if mention.head_pos == 'pron':
                topic = quote.get_topic()
                if mention.get_person() == '1':
                    if source is not None:
                        update_coref_class(coref_class, mention, source)
                    if topic is not None:
                        mention.coreference_prohibited.append(topic)
                    if addressee is not None:
                        mention.coreference_prohibited.append(addressee)
                elif mention.get_person() == '2':
                    if source is not None:
                        mention.coreference_prohibited.append(source)
                    if topic is not None:
                        mention.coreference_prohibited.append(topic)
                    if addressee is not None:
                        update_coref_class(coref_class, mention, addressee)
                elif mention.get_person() == '3':
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
        overall_id = sorted(merges)[0]
        if not coref_classes.get(overall_id) is None:
            for cid in merges:
                if cid != overall_id:
                    #FIXME; check when this is happening and whether it leads to missing coreferences
                    if not coref_classes.get(cid) is None:
                        coref_classes[overall_id] = coref_classes[overall_id] | coref_classes.get(cid)
                        coref_classes[cid] = None
            new_set = coref_classes.get(overall_id)
        #reset mention coreference class to selected id
            for mention_id in new_set:
                my_mention = mentions.get(mention_id)
                my_mention.in_coref_class = [overall_id]


def identify_span_matching_mention(span, mid, mentions):

    matching_mentions = []
    for ment_id, mention in mentions.items():
        if not ment_id == mid:
            if set(mention.get_span()) == set(span):
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
    if len(mention1.get_in_coref_class()) > 0:
        for c_class in mention1.get_in_coref_class():
            if coref_classes[c_class] is not None:
                coref_id = c_class
    else:
        for matching_ment in matches:
            myMention = mentions.get(matching_ment)
            if len(myMention.get_in_coref_class()) > 0:
                for c_coref in myMention.get_in_coref_class():
                    if coref_classes.get(c_coref) is not None:
                        coref_id = c_coref
    if coref_id is None:
        coref_id = len(coref_classes)
    if not mention1.id in coref_classes[coref_id]:
        coref_classes[coref_id].add(mention1.id)
        if not coref_id in mention1.get_in_coref_class():
            mention1.in_coref_class.append(coref_id)
    for matching in matches:
        if not matching in coref_classes[coref_id]:
            coref_classes[coref_id].add(matching)
            matchingMention = mentions.get(matching)
            if not coref_id in matchingMention.get_in_coref_class():
                matchingMention.in_coref_class.append(coref_id)

def identify_appositive_structures(mentions, coref_classes):
    '''
    Assigns coreference for appositive structures
    :param mentions: mentions dictionary
    :param coref_classes: dictionary of coreference class with all coreferring mentions as value
    :return: None (mentions and coref_classes objects are updated)
    '''
    for mid, mention in mentions.items():
        if len(mention.get_appositives()) > 0:
            for appositive in mention.get_appositives():
                matching_mentions = identify_span_matching_mention(appositive, mid, mentions)
                if len(matching_mentions) > 0:
                    update_matching_mentions(mentions, matching_mentions, mention, coref_classes)

def identify_predicative_structures(mentions, coref_classes):
    '''
    Assigns coreference for predicative structures
    :param mentions: dictoinary of mentions
    :param coref_classes: dictionary of coreference class with all coreferring mentions as value
    :return: None (mentions and coref_classes objects are updated)
    '''
    for mid, mention in mentions.items():
        if len(mention.get_predicatives()) > 0:
            for predicative in mention.get_predicatives():
                matching_mentions = identify_span_matching_mention(predicative, mid, mentions)
                if len(matching_mentions) > 0:
                    update_matching_mentions(mentions, matching_mentions, mention, coref_classes)


def get_closest_match_relative_pronoun(mentions, matching, mention_index):

    candidates = {}
    for mid in matching:
        mention = mentions.get(mid)
        offset = mention.head_id
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
        if mention.is_relative_pronoun():
            matching = []
            for om, othermention in mentions.items():
                if not om == m and not mention.head_id in othermention.get_span():
                    for mod in othermention.get_modifiers():
                        if mention.head_id in mod:
                            matching.append(om)
            if len(matching) == 1:
                update_matching_mentions(mentions, matching, mention, coref_classes)
            elif len(matching) > 1:
                mention_index = mention.head_id
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
        if mention.is_reflective_pronoun():
            matching = []
            sent_nr = mention.get_sentence_number()
            for om, othermention in mentions.items():
                if othermention.get_sentence_number() == sent_nr:
                    if not om == m and not mention.head_id in othermention.get_span():
                        if int(othermention.head_id) < mention.head_id:
                            matching.append(om)
            if len(matching) == 1:
                update_matching_mentions(mentions, matching, mention, coref_classes)
            elif len(matching) > 1:
                mention_index = mention.head_id
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
        if mention.get_entity_type() in ['PER','ORG','LOC','MISC'] and len(mention.get_modifiers()) > 0:
            final_matches = []
            for mod in mention.get_modifiers():
                matching_mentions = identify_span_matching_mention(mod, m, mentions)
                for matchid in matching_mentions:
                    mymatch = mentions.get(matchid)
                    if mymatch.get_entity_type() in ['PER','ORG','LOC','MISC']:
                        final_matches.append(matchid)
            if len(final_matches) > 0:
                update_matching_mentions(mentions, final_matches, mention, coref_classes)


def get_sentence_mentions(mentions):

    sentenceMentions = defaultdict(list)

    for mid, mention in mentions.items():
        snr = mention.get_sentence_number()
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
    head_string = id2string.get(mention.head_id)
    non_stop_words = get_string_from_ids(mention.get_no_stop_words())
    main_mods = get_string_from_ids(mention.get_main_modifiers())
    antecedents = []
    for mid, comp_mention in mentions.items():
        #offset must be smaller to be antecedent and not i-to-i
        if comp_mention.head_id < mention.head_id and not mention.head_id <= comp_mention.get_end_offset():
            if head_string == id2string.get(comp_mention.head_id):
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
        if not mention.get_head_pos() == 'pron':
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

    boffset = mention.get_begin_offset()
    eoffset = mention.get_end_offset()
    full_head_string = get_string_from_ids(mention.get_full_head())
    contains_numbers = contains_number(mention.span)

    coreferents = []

    for mid, comp_mention in mentions.items():
        if not mid == mention.id and comp_mention.get_entity_type() in ['PER','ORG','LOC']:
            #mention may not be included in other mention
            if not comp_mention.get_begin_offset() <= boffset and comp_mention.get_end_offset() >= eoffset:
                match = True
                comp_string = get_string_from_ids(comp_mention.get_full_head())
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
        if mention.get_entity_type() in ['PER','ORG','LOC','MISC']:
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

    boffset = mention.get_begin_offset()
    full_head_string = get_string_from_ids(mention.get_full_head())
    non_stop_words = get_string_from_ids(mention.get_no_stop_words())
    antecedents = []

    for mid, comp_mention in mentions.items():
        #we want only antecedents
        if comp_mention.get_end_offset() < boffset:
            if comp_mention.get_entity_type() == mention.get_entity_type():
                match = True
                full_comp_head = get_string_from_ids(comp_mention.get_full_head())
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
        if mention.get_entity_type in ['PER','ORG','LOC','MISC']:
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

    if not is_compatible(mention1.get_number(), mention2.get_number()):
        return False
    if not is_compatible(mention1.get_gender(), mention2.get_gender()):
        return False
    #speaker/addressee 1/2 person was taken care of earlier on
    if not is_compatible(mention1.get_person(), mention2.get_person()):
        return False
    if not is_compatible(mention1.get_entity_type(), mention2.get_entity_type()):
        return False

    return True


def get_candidates_and_distance(mention, mentions):

    candidates = {}
    sent_nr = mention.get_sentence_number()
    for mid, comp_mention in mentions.items():
        if mention.head_id > comp_mention.head_id:
            csnr = comp_mention.get_sentence_number()
            #only consider up to 3 preceding sentences
            if csnr <= sent_nr <= csnr + 3:
                #check if not prohibited
                if not mid in mention.coreference_prohibited:
                    if check_compatibility(mention, comp_mention):
                        candidates[mid] = comp_mention.head_id

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
    mention_index = mention.head_id
    antecedent = identify_closest_candidate(mention_index, candidates)

    return antecedent


def resolve_pronoun_coreference(mentions, coref_classes):

    for mention in mentions.values():
        #we only deal with unresolved pronouns here
        if mention.get_head_pos() == 'pron' and len(mention.in_coref_class) == 0:
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

    #sieve 1: Speaker Identification
    coref_classes = direct_speech_interpretation(quotations, mentions)
    update_mentions(mentions, coref_classes)

    #sieve 2: String Match
    match_full_name_overlap(mentions, coref_classes)
    clean_up_coref_classes(coref_classes, mentions)
    update_mentions(mentions, coref_classes)

    #sieve 3: Relaxed String Match
    match_relaxed_string(mentions, coref_classes)
    clean_up_coref_classes(coref_classes, mentions)
    update_mentions(mentions, coref_classes)

    #sieve 4: Precise constructs
    apply_precise_constructs(mentions, coref_classes)
    clean_up_coref_classes(coref_classes, mentions)
    update_mentions(mentions, coref_classes)

    #sieve 5-7: Strict Head Match
    apply_strict_head_match(mentions, coref_classes)
    clean_up_coref_classes(coref_classes, mentions)
    update_mentions(mentions, coref_classes)

    #sieve 8: Proper Head Word Match
    apply_proper_head_word_match(mentions, coref_classes)
    clean_up_coref_classes(coref_classes, mentions)
    update_mentions(mentions, coref_classes)

    #sieve 9: Relaxed Head Match
    apply_relaxed_head_match(mentions, coref_classes)
    clean_up_coref_classes(coref_classes, mentions)
    update_mentions(mentions, coref_classes)

    #sieve 10
    add_coref_prohibitions(mentions, coref_classes)
    resolve_pronoun_coreference(mentions, coref_classes)
    clean_up_coref_classes(coref_classes, mentions)
    update_mentions(mentions, coref_classes)

    return coref_classes, mentions


def process_coreference(nafin):
    """
    Process coreferences and add to the given NAF.
    Note that coreferences are added in place, and the NAF is returned for convenience
    """
    coref_classes, mentions = resolve_coreference(nafin)
    add_coreference_to_naf(nafin, coref_classes, mentions)
    return nafin
    

def main(argv=None):
    #args and options left for later
    nafin = KafNafParser(sys.stdin)
    nafin = process_coreference(nafin)
    nafin.dump()

if __name__ == '__main__':
    main()
