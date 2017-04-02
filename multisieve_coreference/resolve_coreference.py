import sys
from KafNafParserPy import *
from collections import defaultdict
from naf_info import get_mentions, add_coreference_to_naf, identify_direct_quotations


def match_full_name_overlap(mentions, coref_classes):
    '''
    Function that places entities with full string match in the same coreference group
    :param mentions: dictionary of mention objects (key is mention id)
    :return:
    '''
    found_entities = {}

    #FIXME: verify (when evaluating) whether prohibited needs to be taken into account here
    for mid, mention in mentions.items():
        if mention.entity_type is not None:
            if mention.string in found_entities:
                coref_id = found_entities.get(mention.string)
                if len(mention.in_coref_class) > 0:
                    #if it's the same chain, nothing remains to be done
                    #else update one dictionary and mark double class; classes can be merged in later step
                    if mention.in_coref_class[0] != coref_id:
                        mention.in_coref_class.append(coref_id)
                        coref_classes[coref_id].append(mention.id)
                else:
                    mention.in_coref_class.append(coref_id)
                    coref_classes[coref_id].append(mention.id)
            else:
                #coref classes will usually have a length 1; if not, it doesn't matter which one is picked
                if len(mention.in_coref_class) > 0:
                    coref_nr = mention.in_coref_class[0]
                else:
                    coref_nr = len(coref_classes)
                    mention.in_coref_class.append(coref_nr)
                coref_classes[coref_nr].append(mention.id)
                found_entities[mention.string] = coref_nr

    return found_entities


def relaxed_string_match(mentions):
    '''
    Function that places entities that match if post-head modifiers (PPs and relative clauses) are removed
    :param mentions:
    :return:
    '''
    print('blah')


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
        coref_class[coref_class_id].append(current_mention.id)
        coref_class[coref_class_id].append(coref_mention)

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
    coref_classes = defaultdict(list)
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
                    updated_nml = set(nml) + set(to_merge)
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
        for cid in merges:
            if cid != overall_id:
                coref_classes[overall_id] += coref_classes.get(cid)
                coref_classes[cid] = None
        new_set = coref_classes.get(overall_id)
        #reset mention coreference class to selected id
        for mention_id in new_set:
            my_mention = mentions.get(mention_id)
            my_mention.in_coref_class = [overall_id]




def resolve_coreference(nafin):

    mentions = get_mentions(nafin)
    quotations = identify_direct_quotations(nafin, mentions)

    #sieve 1: Speaker Identification
    coref_classes = direct_speech_interpretation(quotations, mentions)
    update_mentions(mentions, coref_classes)

    #sieve 2: String Match
    full_entities = match_full_name_overlap(mentions, coref_classes)
    clean_up_coref_classes(coref_classes, mentions)
    update_mentions(mentions, coref_classes)

    #sieve 3: Relaxed String Match



    return coref_classes, mentions


def main(argv=None):

    #args and options left for later

    nafin = KafNafParser(sys.stdin)
    coref_classes, mentions = resolve_coreference(nafin)
    add_coreference_to_naf(nafin, coref_classes, mentions)
    nafin.dump()

if __name__ == '__main__':
    main()