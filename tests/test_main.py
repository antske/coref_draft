import sys
import subprocess

import pytest


from multisieve_coreference.resolve_coreference import process_coreference


def test_main_example(example_naf_file, temp_file, example_naf_output):
    with open(example_naf_file) as fd, open(temp_file, 'w') as out:
        subprocess.check_call(
            [sys.executable, '-m', 'multisieve_coreference'],
            stdin=fd,
            stdout=out
        )
    from KafNafParserPy import KafNafParser
    with open(temp_file) as out, open(example_naf_output) as correct:
        assert KafNafParser(out).coreference_layer is not None
        out.seek(0)
        assert out.read() == correct.read()


def test_example(example_naf_object, caplog):
    # caplog.set_level('DEBUG')
    caplog.set_level('WARNING', 'multisieve_coreference.constituency_tree')
    out = process_coreference(example_naf_object)
    assert out.coreference_layer is not None


@pytest.mark.slow
def test_main_sonar1(sonar_naf_object1, caplog):
    # caplog.set_level('DEBUG')
    caplog.set_level('WARNING', 'multisieve_coreference.constituency_tree')
    out = process_coreference(sonar_naf_object1)
    assert out.coreference_layer is not None


@pytest.mark.slow
def test_main_sonar2(sonar_naf_object2, caplog):
    # caplog.set_level('DEBUG')
    caplog.set_level('WARNING', 'multisieve_coreference.constituency_tree')
    out = process_coreference(sonar_naf_object2)
    assert out.coreference_layer is not None
