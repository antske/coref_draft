import itertools as it
from .dump import get_terms_from_offsets


def term_id_to_tokens(nafobj, term_id):
    term = nafobj.get_term(term_id)
    if term is None:
        raise ValueError("No term with that ID: {!r}".format(term_id))
    return [
        (ID, nafobj.get_token(ID).get_text())
        for ID in term.get_span_ids()
    ]


def safe_term_id_to_tokens(*args, **kwargs):
    try:
        return term_id_to_tokens(*args, **kwargs)
    except ValueError:
        return []


def view_mentions(nafobj, mentions):
    """
    Content of mention constituent on separate lines
    """
    return '\n'.join(
        view_mention(nafobj, mID, mention)
        for mID, mention in mentions.items()
    )


def view_mention(nafobj, mention_ID, mention):
    return '{}: {!r}'.format(
        mention_ID,
        list(it.chain(*(
            term_id_to_tokens(nafobj, termID)
            for termID in get_terms_from_offsets(nafobj, mention.span)[0]
        )))
    )


def view_coref_classes(nafobj, mentions, coref_classes):
    """
    Content of mention constituent on separate lines
    """
    return '\n'.join(
        str(cID) + ':\n\t' + '\n\t'.join(
            view_mention(nafobj, mID, mentions[mID])
            for mID in mention_ids
        )
        for cID, mention_ids in coref_classes.items()
    )
