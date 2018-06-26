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


**!! NB !!** Singleton clusters are left out by default. To Include singleton clusters pass `-s` or `--include_singletons` on the command line or call `process_coreference(naf_object, include_singletons=True)`.


Contact
------

* Antske Fokkens
* antske.fokkens@vu.nl
* antske@gmail.com
* http://antskefokkens.info
* Vrije University of Amsterdam

Issues
------
 - [ ] `global stop_words` should be a `set`
 - [ ] `linguisticProcessors` layer should be added to `nafHeader`
 - [ ] `create_mention` docstring
 - [ ] `fem` and `masc` do not appear in output of Alpino, but _are_ used to identify gender
 - [ ] `update_coref_class`: `if len(coref_mention) > 0:` seems very icky

License
------
Sofware distributed under Apache License v2.0, see LICENSE file for details.
