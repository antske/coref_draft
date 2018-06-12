import sys
import subprocess


def test_main(naf_file, temp_file, naf_example_output):
    with open(naf_file) as fd, open(temp_file, 'w') as out:
        subprocess.check_call(
            [sys.executable, '-m', 'multisieve_coreference'],
            stdin=fd,
            stdout=out
        )
    from KafNafParserPy import KafNafParser
    with open(temp_file) as out, open(naf_example_output) as correct:
        assert KafNafParser(out).coreference_layer is not None
        out.seek(0)
        assert out.read() == correct.read()
