import logging

from KafNafParserPy import Cspan, Ctarget, Ccoreference


logger = logging.getLogger(None if __name__ == '__main__' else __name__)


def add_coreference_to_naf(nafobj, corefclasses, mentions):

    # FIXME: (detail) for readability, add coreference chains in order
    start_count = get_starting_count(nafobj)
    coref_according_to_index = get_ordered_coreference_chains(
        corefclasses,
        mentions
    )
    if logger.getEffectiveLevel() <= logging.DEBUG:
        from .util import view_coref_classes
        from collections import OrderedDict
        logger.debug("Coreference classes: {}".format(
            view_coref_classes(
                nafobj,
                OrderedDict(sorted(coref_according_to_index.items())),
                mentions
            )
        ))

    for key in sorted(coref_according_to_index):
        mids = coref_according_to_index.get(key)
        if mids is not None:
            mids = set(mids)
            if len(mids) > 1:
                nafCoref = Ccoreference()
                cid = 'co' + str(start_count)
                start_count += 1
                nafCoref.set_id(cid)
                nafCoref.set_type('entity')
                data = sorted(
                    get_terms_from_offsets(
                        nafobj,
                        mention.span,
                        mention.head_offset
                    )
                    for mention in map(mentions.get, mids)
                )
                for term_id_span, head_id in data:
                    coref_span = create_span(term_id_span, head_id)
                    nafCoref.add_span_object(coref_span)
                nafobj.add_coreference(nafCoref)


def create_span(term_id_span, head_id):
    '''
    Creates naf span object where head id is set
    :param term_id_span: list of term ids
    :param head_id: identifier for the head id
    :return: naf span object
    '''

    mySpan = Cspan()
    for term in term_id_span:
        if term == head_id:
            myTarget = Ctarget()
            myTarget.set_id(term)
            myTarget.set_as_head()
            mySpan.add_target(myTarget)
        else:
            mySpan.add_target_id(term)
    return mySpan


def get_ordered_coreference_chains(corefclasses, mentions):
    '''
    Function that creates new coreference dictionary with index of first
    mention as key (for ordering)

    :param corefclasses: identified coreference classes
    :return: dictionary of coreference classes with new indeces
    '''

    coref_dict = {}

    for mids in corefclasses.values():
        if mids is not None:
            first_index = 90000000000
            for mid in mids:
                mention = mentions.get(mid)
                if mention.head_offset < first_index:
                    first_index = mention.head_offset
            coref_dict[first_index] = mids

    return coref_dict


def get_starting_count(nafobj):

    coref_counter = 1
    for coref in nafobj.get_corefs():
        coref_counter += 1

    return coref_counter


def get_terms_from_offsets(nafobj, offset_span, head_offset=-1):

    wids = []
    head_wid = ''
    for token in nafobj.get_tokens():
        if int(token.get_offset()) in offset_span:
            wids.append(token.get_id())
            if int(token.get_offset()) == head_offset:
                head_wid = token.get_id()

    tids = []
    head_tid = ''
    for term in nafobj.get_terms():
        if term.get_span().get_span_ids()[0] in wids:
            tids.append(term.get_id())
        if head_wid in term.get_span().get_span_ids():
            head_tid = term.get_id()

    return tids, head_tid
