coref_draft
=============

Description
----------
Implementation of Stanford multi-seive coreference resolution approach for Dutch.
This is a draft version of the code. An official first release will be made available on github/cltl upon completion and basic testing of the first version of the system.


Current implementation
----------------------

The current implementation works on naf input files parsed by Alpino (i.e. it works for Dutch).

Future plans:

- separate Alpino specific functions from general naf-extraction functions (extend to other languages)
- create library for English

Usage
----

From command line:

```{bash}
$ python multisieve_coreference < inputfile.naf
```

From python:

```{python}
from multisieve_coreference import process_coreference
process_coreference(naf_object)
```

Calling `process_coreference` will change the naf_object in-place by adding coref nodes (if any).

Gaps in mention spans (mostly left-out punctuation marks) are not filled by default. To make sure mentions only refer to consecutive spans, pass `-f` or `--fill-gaps` on the command line or call `process_coreference(naf_object, fill_gaps=True)`.

**!! NB !!** Singleton clusters are left out by default. To Include singleton clusters pass `-s` or `--include_singletons` on the command line or call `process_coreference(naf_object, include_singletons=True)`.


Issues
------
 - [ ] Mentions are not ordered at all, in contrast to the description of the algorithm by Lee et al. (2013)
 - [ ] Mention attributes are not shared among mentions in the same coreference class, in contrast to the description of the algorithm by Lee et al. (2013)
 - [ ] `global stop_words` should be a `set` (and not a global) and doesn't seem to be used consistently.
 - [ ] `linguisticProcessors` layer should be added to `nafHeader`
 - [ ] `create_mention` docstring
 - [ ] `fem` and `masc` do not appear in output of Alpino, but _are_ used to identify gender
 - [ ] Many variables and functions use `id` in their name while they actually contain or use offsets.
 - [ ] Duplicate code in `resolve_relative_pronoun_structures` and `resolve_reflective_pronoun_structures`
 - [ ] `get_predicative_information` seems to miss some constructs
 - [ ] `dep2heads` shouldn't need lists as values because a dependency _tree_ is a tree.
 - [X] Add punctuation marks to mention spans in post processing **if** they are in the middle of the mention. They aren't in the span in the first place because punctuation is filtered out of the dependency tree to make sure punctuation that isn't in the middle of a mention is not included.
 - [ ] `Cmention.coreference_prohibited` does not seem to be used.
 - [ ] `post_process` should only allow adding punctuation in the gaps of a span
 - [ ] `check_if_quotation_contains_dependent` is a mess.


Design ideal
------------
It would be great if all changing information (mostly related to which mentions should or should not be in the same coreference class) is kept in one object, instead of spread out amongst the mention objects themselves. (This is currently the case with `Cmention.coreference_prohibited`.)

It would be even nicer if every sieve would inherit from some `Sieve` abstraction and these sieves could be easily plugged and played by moving them around in some input sequence.


Contact
------

* Antske Fokkens
* antske.fokkens@vu.nl
* antske@gmail.com
* http://antskefokkens.info
* Vrije University of Amsterdam

License
------
Sofware distributed under Apache License v2.0, see LICENSE file for details.


References
----------

Heeyoung Lee, Angel Chang, Yves Peirsman, Nathanael Chambers, Mihai Surdeanu, and Dan Jurafsky. 2013. Deterministic coreference resolution based on entity-centric, precision-ranked rules. Comput. Linguist. 39, 4 (December 2013), 885-916. DOI=http://dx.doi.org/10.1162/COLI_a_00152
