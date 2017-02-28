# Copyright (C) 2017 by Kevin L. Mitchell <klmitch@mit.edu>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you
# may not use this file except in compliance with the License. You may
# obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

import os

import cli_tools

from hypocrite import hypofile


@cli_tools.argument(
    'infile',
    help='The input test file.'
)
@cli_tools.argument(
    '--output', '-O',
    dest='outfile',
    help='The file to write the result to.  If not provided, the input '
    'file name will be altered by changing the extension to ".c" and '
    'will be written to the current directory.'
)
@cli_tools.argument(
    '--debug', '-d',
    help='Enable debugging mode.  Note: This only affects hypocrite '
    'itself; no additional debugging code is added to the written '
    'test file.'
)
def main(infile, outfile=None):
    """
    Generate a C test file from the contents of a specially-formatted
    input file.  The input format supports declaration of fixtures and
    mocks, in addition to the actual tests.

    :param str infile: The name of the input file.
    :param str outfile: The name of the output file.  If not provided,
                        the name of the input file is altered by
                        changing the extension to ".c" and the file
                        will be written out to the current directory.
    """

    # Read in the hypocrite file
    hfile = hypofile.HypoFile.parse(infile)

    # Pick the correct test basename
    if not outfile:
        test_fname = os.path.splitext(os.path.basename(infile))[0]
        outfile = test_fname + '.c'
    else:
        test_fname = os.path.splitext(os.path.basename(outfile))[0]

    # Render the template
    rendered = hfile.render(test_fname)

    # Write it to the appropriate output file
    with open(outfile, 'w') as stream:
        rendered.output(stream, outfile)
