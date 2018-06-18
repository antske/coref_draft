import os
import pytest


@pytest.fixture
def resources_dir():
    return 'resources'


@pytest.fixture
def temp_file():
    import tempfile
    return tempfile.mktemp()


# Example file
@pytest.fixture
def example_naf_file(resources_dir):
    return os.path.join(resources_dir, 'example-in.naf')


@pytest.fixture
def example_naf_output(resources_dir):
    return os.path.join(
        resources_dir,
        'example-out.naf'
    )


@pytest.fixture
def example_naf_object(example_naf_file):
    from KafNafParserPy import KafNafParser
    return KafNafParser(example_naf_file)


# SoNaR files
@pytest.fixture
def sonar_naf_file1(resources_dir):
    return os.path.join(resources_dir, 'SoNaR-dpc-bal-001236-nl-sen-in.naf')


@pytest.fixture
def sonar_naf_object1(sonar_naf_file1):
    from KafNafParserPy import KafNafParser
    return KafNafParser(sonar_naf_file1)


@pytest.fixture
def sonar_naf_file2(resources_dir):
    return os.path.join(resources_dir, 'SoNaR-dpc-cam-001280-nl-sen-in.naf')


@pytest.fixture
def sonar_naf_object2(sonar_naf_file2):
    from KafNafParserPy import KafNafParser
    return KafNafParser(sonar_naf_file2)
