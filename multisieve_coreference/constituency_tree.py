class ConstituencyTree:
    """
    Groups together information from a constituency tree and exposes convenient
    lookups.
    """
    def __init__(self, nafobj, item_filter):
        # Create all dicts
        # self.
        self.head2deps, self.dep2heads = self.create_headdep_dicts(
            nafobj,
            item_filter
        )

    def direct_dependents(self, ID):
        """
        Get the term IDs of the terms directly dependent on `ID`.

        :param headID:  term ID to get direct dependents of
        :return:        a set of IDs that are direct dependents of `ID`
        """
        raise NotImplementedError()

    def direct_dependents_with_relation(self, ID):
        """
        Get the (ID, relation) tuples of the terms directly dependent on `ID`.

        :param headID:  term ID to get direct dependents of
        :return:        a set (ID, relation) tuples that are direct dependents
                        of `ID`
        """
        raise NotImplementedError()

    def constituent(self, ID):
        """
        Get the term IDs of the terms dependent on `ID`.

        :param headID:  term ID to get constituent of
        :return:        a set of IDs of terms that are dependents of `ID`
        """
        raise NotImplementedError()

    def direct_parents(self, ID):
        """
        Get the term IDs of the terms of which `ID` is a direct dependent.

        :param headID:  term ID to get direct dependents of
        :return:        a set of IDs that are direct dependents of `ID`
        """
        raise NotImplementedError()

    @staticmethod
    def create_headdep_dicts(
            nafobj,
            term_filter=lambda naf, t: naf.get_term(t).get_pos() != 'punct'):
        """
        Create dictionaries of dependent to heads and head to direct dependent

        :param nafobj:  nafobj from input file
        :return:        head2deps, dep2heads
        """

        allhead2deps = {}
        dep2headIDs = {}
        for dep in nafobj.get_dependencies():
            headID = dep.get_from()
            toID = dep.get_to()
            allhead2deps[headID].append((toID, dep.get_function()))
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
