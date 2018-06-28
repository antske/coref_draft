import sys
import itertools as it

if sys.version_info >= (3, 3):
    from collections.abc import MutableSet
else:
    from collections import MutableSet


class CoreferenceInformation:
    """
    Class containing information about which mentions refer to the same thing.

    All information is calculated directly from `self.coref_classes` when
    queried, which means `self.coref_classes` can be edited directly.

    Strictly all mentions in a coreference class refer to _exactly_ the same
    thing, which means that two coreference classes should be combined if they
    contain the same mention. This can be done automatically using
    `self.merge()`.
    """

    def __init__(self, coref_classes=None, id_counter=0):
        self.id_counter = id_counter
        self.coref_classes = {} if coref_classes is None else coref_classes
        for cID, mentions in self.coref_classes.items():
            if not isinstance(mentions, MutableSet):
                raise ValueError(
                    "`coref_classes` must be a Mapping of MutableSets."
                    " Coreference class {!r} is of type: {}".format(
                        cID,
                        type(mentions)
                    )
                )

    def __repr__(self):
        return self.__class__.__name__ + '(' \
            '{self.coref_classes}, ' \
            '{self.id_counter}' \
            ')'.format(self=self)

    def classes_of_mention(self, mention_id):
        """
        Get the set of coreference class IDs that the given mention is part of.

        :param mention_id: mention ID to get coreference classes of
        :return: IDs of coreference classes `mention_id` is part of
        """
        return frozenset(
            cID
            for cID, coref_class in self.coref_classes.items()
            if mention_id in coref_class
        )

    def referenced_mentions(self):
        return frozenset(it.chain.from_iterable(self.coref_classes.values()))

    def add_coref_class(self, mentions=None, merge=True):
        """
        Create a new coreference class with the given mentions.

        Immediately merges all coreference classes with `self.merge`

        :param mentions: mentions to put in the new coreference class
        :param merge:    whether to immediately call `self.merge`
        :return:         ID of the newly created coreference class
        """
        cID = self.get_new_id()
        self.coref_classes[cID] = set() \
            if mentions is None \
            else set(mentions)
        if merge:
            cID = self.merge().get(cID, cID)
        return cID

    def get_new_id(self):
        """
        Get an unused coreference class ID
        """
        ID = 'c{}'.format(self.id_counter)
        self.id_counter += 1
        return ID

    def merge(self):
        """
        Merge all coreference classes that contain the same mention.

        :return:    mapping of {original ID: new ID} for removed IDs only
        """
        # This is O(n * m), with n the number of coreference classes and
        # m the total number of mentions :(
        classes_to_merge = {
            classes
            for classes in map(
                self.classes_of_mention,
                self.referenced_mentions()
            )
            if len(classes) > 1
        }

        return merge_keys(self.coref_classes, classes_to_merge)


def merge_keys(dictionary, sets_of_keys):
    """
    Given a set of sets of keys that should be merged, merge the given
    dictionary of sets in place.

    :param dictionary:      dictionary to merge
    :param sets_of_keys:    which keys should be combined
    :return:                mapping of {original ID: new ID} for removed IDs
    """
    sets_of_keys = set(map(frozenset, sets_of_keys))
    id_map = {}

    while sets_of_keys:
        # Find what to merge
        keys = sets_of_keys.pop()

        # Randomly choose a coreference class
        try:
            chosen_one = next(iter(keys))
        except StopIteration:
            # No keys to merge
            continue
        other_keys = keys - {chosen_one}
        del keys

        # Merge
        chosen_set = dictionary[chosen_one]
        for key in other_keys:
            chosen_set |= dictionary.pop(key)

        if other_keys:
            # Update the sets of keys
            sets_of_keys = {
                frozenset(
                    chosen_one if key in other_keys else key
                    for key in keys
                )
                for keys in sets_of_keys
            }

            # Update old IDs
            id_map = {
                original: chosen_one if key in other_keys else key
                for original, key in id_map.items()
            }
            # Add new IDs
            id_map.update(zip(other_keys, it.repeat(chosen_one)))
    return id_map
