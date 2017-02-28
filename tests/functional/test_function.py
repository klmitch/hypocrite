import os

from hypocrite import main

TEST_INPUT = 'test.hypo'
TEST_OUTPUT = 'test.c'
ALTERNATE_OUTPUT = 'alternate.c'


def test_base(datadir, tmpdir):
    # Change directories to the tmpdir
    with tmpdir.as_cwd():
        # Run hypocrite on an example file
        main.main(os.path.join(datadir, TEST_INPUT))

    # Test that the expected output file was created
    outfile = tmpdir.join(TEST_OUTPUT)
    assert outfile.check(file=1)

    # Test that the expected output was generated
    out_text = outfile.read()
    with open(os.path.join(datadir, TEST_OUTPUT)) as f:
        out_expected = f.read()
    assert out_text == out_expected


def test_explicit_output(datadir, tmpdir):
    # Change directories to the tmpdir
    with tmpdir.as_cwd():
        # Run hypocrite on an example file
        main.main(os.path.join(datadir, TEST_INPUT), ALTERNATE_OUTPUT)

    # Test that the expected output file was created
    outfile = tmpdir.join(ALTERNATE_OUTPUT)
    assert outfile.check(file=1)

    # Test that the expected output was generated
    out_text = outfile.read()
    with open(os.path.join(datadir, ALTERNATE_OUTPUT)) as f:
        out_expected = f.read()
    assert out_text == out_expected
