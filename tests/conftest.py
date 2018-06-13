import os
import pytest


@pytest.fixture
def resources_dir():
    return 'resources'


@pytest.fixture
def naf_file(resources_dir):
    return os.path.join(resources_dir, 'example-in.naf')


@pytest.fixture
def naf_example_output(resources_dir):
    return os.path.join(
        resources_dir,
        'example-out.naf'
    )


@pytest.fixture
def naf_string(naf_file):
    with open(naf_file) as fd:
        return fd.read()


@pytest.fixture
def naf_object(naf_file):
    from KafNafParserPy import KafNafParser
    return KafNafParser(naf_file)


@pytest.fixture
def temp_file():
    import tempfile
    return tempfile.mktemp()
