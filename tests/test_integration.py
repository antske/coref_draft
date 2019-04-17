import os
import pytest
from run_and_compare import run_and_compare


@pytest.fixture
def in_dir(resources_dir):
    return os.path.join(resources_dir, 'easy-sentences/NAFin')


@pytest.fixture
def correct_out_dir(resources_dir):
    return os.path.join(resources_dir, 'easy-sentences/NAFout')


@pytest.mark.slow
def test_integration(in_dir, correct_out_dir, temp_file):
    for filename in os.listdir(in_dir):
        infile = os.path.join(in_dir, filename)
        correct_outfile = os.path.join(correct_out_dir, filename)

        assert os.path.exists(infile)
        assert os.path.exists(correct_outfile)

        run_and_compare(infile, temp_file, correct_outfile)
