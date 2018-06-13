import logging

logger = logging.getLogger(None if __name__ == '__main__' else __name__)


class ConstituencyTree:
    """
    Group together information from a constituency tree and expose convenient
    lookups.
    """
    def __init__(self, nafobj, term_filter=lambda naf, t: True):
        """
        Initialise `ConstituencyTree`.

        Only keep terms where `term_filter(term)` evaluates True.

        :param nafobj:          NAF object from input
        :param term_filter:     filter for terms
        """
        # Create all dicts
        # self.
        self.head2deps, self.dep2heads = self.create_headdep_dicts(
            nafobj,
            term_filter
        )
        logger.debug(self.head2deps, self.dep2heads)
        self.head2constituent = {}

    def get_direct_dependents(self, ID):
        """
        Get the term IDs of the terms directly dependent on `ID`.

        :param headID:  term ID to get direct dependents of
        :return:        a set of IDs that are direct dependents of `ID`
        """
        raise NotImplementedError()

    def get_direct_dependents_with_relation(self, ID):
        """
        Get the (ID, relation) tuples of the terms directly dependent on `ID`.

        :param headID:  term ID to get direct dependents of
        :return:        a set (ID, relation) tuples that are direct dependents
                        of `ID`
        """
        raise NotImplementedError()

    def get_constituent(self, ID):
        """
        Get the term IDs of the terms dependent on `ID`.

        Always contains `ID`, even if it is an unknown `ID`.

        :param headID:  term ID to get constituent of
        :return:        a set of IDs of terms that are dependents of `ID`
        """
        try:
            return self.head2constituent[ID]
        except KeyError:
            return self._get_constituent(ID, set())

    def _get_constituent(self, ID, parents):
        """
        Calculate the constituent if it is not in the cache

        :param head:      head to find constituent of
        :param parents:   term IDs that are already being calculated, thus
                          should not be recursed into
        :return:          set of term IDs that are in the constituent of `head`
        """
        if ID in parents:
            # Prevent loop
            return set()
        elif ID in self.head2constituent:
            # Use cache
            return self.head2constituent[ID]
        # Base case: direct dependents
        deps = {term_id for term_id, _ in self.head2deps.get(ID, [])}
        # Recursive step: call _get_constituent for every direct dependent
        deps.union(*(
            self._get_constituent(term_id, parents | {term_id})
            for term_id in deps
        ))
        # Make sure ID itself is in it
        deps.add(ID)
        # Cache
        self.head2constituent[ID] = deps
        return deps

    def get_direct_parents(self, ID):
        """
        Get the term IDs of the terms of which `ID` is a direct dependent.

        :param headID:  term ID to get direct dependents of
        :return:        a set of IDs that are direct dependents of `ID`
        """
        raise NotImplementedError()

    @staticmethod
    def create_headdep_dicts(nafobj, term_filter):
        """
        Create dictionaries of dependent to heads and head to direct dependent

        Only keep terms where `term_filter(term)` evaluates True.

        :param nafobj:          NAF object from input
        :param term_filter:     filter for terms
        :return:        head2deps, dep2heads
        """

        allhead2deps = {}
        dep2headIDs = {}
        for dep in nafobj.get_dependencies():
            headID = dep.get_from()
            toID = dep.get_to()
            allhead2deps.setdefault(headID, []).append(
                (toID, dep.get_function())
            )
            dep2headIDs.setdefault(toID, []).append(headID)

        head2deps = {}
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
        dep2heads = {}
        for headID, deps in head2deps.items():
            for toID, relation in deps:
                dep2heads.setdefault(toID, set()).add((headID, relation))

        return head2deps, dep2heads