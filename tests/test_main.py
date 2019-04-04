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


def test_example_without_fill(example_naf_object, caplog):
    caplog.set_level('DEBUG', 'multisieve_coreference.dump')
    process_coreference(example_naf_object, fill_gaps=False)
    assert example_naf_object.coreference_layer is not None


@pytest.mark.slow
def test_main_sonar1_without_fill(sonar_naf_object1, caplog):
    caplog.set_level('DEBUG', 'multisieve_coreference.dump')
    process_coreference(sonar_naf_object1, fill_gaps=False)
    assert sonar_naf_object1.coreference_layer is not None


def test_main_sonar2_without_fill(sonar_naf_object2, caplog):
    caplog.set_level('DEBUG', 'multisieve_coreference.dump')
    process_coreference(sonar_naf_object2, fill_gaps=False)
    assert sonar_naf_object2.coreference_layer is not None


@pytest.mark.slow
def test_main_sonar3_without_fill(sonar_naf_object3, caplog):
    caplog.set_level('DEBUG', 'multisieve_coreference.dump')
    process_coreference(sonar_naf_object3, fill_gaps=False)
    assert sonar_naf_object3.coreference_layer is not None


def test_example_with_fill(example_naf_object, caplog):
    caplog.set_level('DEBUG', 'multisieve_coreference.dump')
    process_coreference(example_naf_object, fill_gaps=True)
    assert example_naf_object.coreference_layer is not None


@pytest.mark.slow
def test_main_sonar1_with_fill(sonar_naf_object1, caplog):
    caplog.set_level('DEBUG', 'multisieve_coreference.dump')
    process_coreference(sonar_naf_object1, fill_gaps=True)
    assert sonar_naf_object1.coreference_layer is not None


def test_main_sonar2_with_fill(sonar_naf_object2, caplog):
    caplog.set_level('DEBUG', 'multisieve_coreference.dump')
    process_coreference(sonar_naf_object2, fill_gaps=True)
    assert sonar_naf_object2.coreference_layer is not None


@pytest.mark.slow
def test_main_sonar3_with_fill(sonar_naf_object3, caplog):
    caplog.set_level('DEBUG', 'multisieve_coreference.dump')
    process_coreference(sonar_naf_object3, fill_gaps=True)
    assert sonar_naf_object3.coreference_layer is not None
