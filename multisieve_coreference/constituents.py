import logging
from collections import defaultdict

logger = logging.getLogger(None if __name__ == '__main__' else __name__)

head2constituent = dict()
head2deps = dict()
dep2heads = dict()


def get_constituent(head):
    """
    Get all the terms in the constituent of which `head` is the head.
    """
    global head2constituent
    try:
        return head2constituent[head]
    except KeyError:
        return recursively_get_constituent(head, set())


def recursively_get_constituent(head, parents):
    """
    Calculate the constituent if it is not in the cache

    :param head:        head to find constituent of
    :param parents:     term IDs that are already being calculated, thus should
                        not be recursed into
    :return:            set of term IDs that are in the constituent of `head`
    """
    global head2constituent, head2deps
    logger.debug("Head: {}".format(head))
    if head in parents:
        return set()
    elif head in head2constituent:
        return head2constituent[head]
    # Base case: direct dependents
    deps = {term_id for term_id, _ in head2deps.get(head, [])}
    # Recursive step: call _get_constituent for every direct dependent
    parents.add(head)
    deps.update(*(
        recursively_get_constituent(term_id, parents)
        for term_id in deps
    ))
    # Make sure head itself is in it
    deps.add(head)
    # Cache
    head2constituent[head] = deps
    return deps


def create_headdep_dicts(
        nafobj,
        term_filter=lambda naf, t: naf.get_term(t).get_pos() != 'punct'):
    '''
    Function that creates dictionaries of dep to heads and head to deps
    :param nafobj: nafobj from input file
    :return: None
    '''

    allhead2deps = defaultdict(list)
    # To make sure we get a KeyError if something goes (horribly) wrong
    dep2headIDs = dict()
    for dep in nafobj.get_dependencies():
        headID = dep.get_from()
        toID = dep.get_to()
        allhead2deps[headID].append((toID, dep.get_function()))
        dep2headIDs.setdefault(toID, []).append(headID)

    global head2deps
    for headID, deps in allhead2deps.items():
        # I don't have to do something with the deps that are filtered out,
        # because if they are leaves they can just be deleted and if they
        # aren't leaves they will also appear as headID and handled there.
        deps = {
            (toID, relation)
            for toID, relation in deps
            if term_filter(nafobj, toID)
        }
        if term_filter(nafobj, headID):
            head2deps.setdefault(headID, set()).update(deps)
        else:
            # Delete the head by adding its dependents to the heads of the
            # head.
            for super_headID in dep2headIDs[headID]:
                if term_filter(nafobj, super_headID):
                    head2deps.setdefault(super_headID, set()).update(deps)

    # Create the reverse too
    global dep2heads
    for headID, deps in head2deps.items():
        for toID, relation in deps:
            dep2heads.setdefault(toID, set()).add((headID, relation))
