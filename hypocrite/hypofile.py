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

import collections
import os

import six

from hypocrite import perfile
from hypocrite import template

# Represent an argument
HypoMockArg = collections.namedtuple('HypoMockArg', ['type_', 'name'])

# Represent a fixture injection
HypoFixtureInjection = collections.namedtuple(
    'HypoFixtureInjection', ['fixture', 'inject']
)


def _extract_type(toks, delims):
    """
    Helper to extract type and name information from a mock
    declaration.  Note that this version can only handle simple type
    declarations; function pointers should be ``typedef``'d.

    :param list toks: The list of tokens from which to extract the
                      type.
    :param set delims: The delimiters to use when extracting the
                       types.

    :returns: An iterator of 3-element tuples.  The first element will
              be a list of tokens forming the type; the second element
              will be a token identified as the argument or function
              name (which may be ``None`` if two delimiters followed
              each other); and the third element will be the
              delimiter.  At the end of iteration, a final element is
              returned with the delimiter set to ``None``.
    """

    # Thin wrapper around split_toks()
    for stack, delim in perfile.split_toks(toks, delims, True):
        yield stack[:-1], stack[-1] if stack else None, delim


def _make_type(toks, directive, coord):
    """
    Construct a type string from a sequence of tokens.

    :param list toks: The list of tokens to form the type string from.
    :param str directive: The name of the directive.  This is used for
                          error reporting.
    :param coord: The coordinates the tokens are from.  This is used
                  for error reporting.
    :type coord: ``Coordinates``

    :returns: A type string.

    :raises HypocriteException:
        An error occurred while parsing the directive.
    """

    type_ = []

    last_tok = None
    for tok in toks:
        # Watch out for bogus token types
        if tok.type_ != perfile.TOK_WORD and tok != (perfile.TOK_CHAR, '*'):
            raise perfile.ParseException(
                'Invalid %%%s directive at %s' % (directive, coord)
            )

        if (last_tok and tok.type_ == perfile.TOK_CHAR and
                last_tok.type_ == perfile.TOK_CHAR):
            # Avoid spaces between subsequent '*' tokens
            type_[-1] += tok.value
        else:
            type_.append(tok.value)

        last_tok = tok

    # Create and return the type string
    return ' '.join(type_)


class Preamble(object):
    """
    Represent a "preamble" directive.  These directives contain
    literal code to include in the preamble for the test file.
    """

    def __init__(self, coord_range, code):
        """
        Initialize a ``Preamble`` instance.

        :param coord_range: The range of coordinates associated with
                            the test in the hypocrite input file.
        :type coord_range: ``hypocrite.location.CoordinateRange``
        :param code: The code to include in the preamble.
        :type code: ``hypocrite.linelist.LineList``
        """

        self.coord_range = coord_range
        self.code = code

    def render(self, hfile, ctxt):
        """
        Render a preamble.  This adds the preamble to the "preamble"
        section of a render context.

        :param hfile: The hypocrite input file.
        :type hfile: ``HypocriteFile``
        :param ctxt: The render context.
        :type ctxt: ``hypocrite.template.RenderContext``
        """

        # Just add the code to the relevant section
        ctxt.sections['preamble'] += self.code


class HypocriteTest(object):
    """
    Represent a "test" directive.  These directives contain the actual
    test file.
    """

    TEMPLATE = 'test.c'

    def __init__(self, coord_range, name, code, fixtures):
        """
        Initialize a ``HypocriteTest`` instance.

        :param coord_range: The range of coordinates associated with
                            the test in the hypocrite input file.
        :type coord_range: ``hypocrite.location.CoordinateRange``
        :param str name: The base name of the test.
        :param code: The code of the test function.
        :type code: ``hypocrite.linelist.LineList``
        :param list fixtures: A list of ``HypoFixtureInjection``
                              instances indicating fixtures that
                              should be used with the test.
        """

        self.coord_range = coord_range
        self.name = name
        self.code = code
        self.fixtures = fixtures

    def render(self, hfile, ctxt):
        """
        Render a test.  This uses a template to render the test into
        actual output code.

        :param hfile: The hypocrite input file.
        :type hfile: ``HypocriteFile``
        :param ctxt: The render context.
        :type ctxt: ``hypocrite.template.RenderContext``
        """

        # Resolve all the fixtures
        fixtures = [
            (hfile.fixtures[fix], inject) for fix, inject in self.fixtures
        ]

        # Load the template and render it
        tmpl = template.Template.get_tmpl(self.TEMPLATE)
        tmpl.render(ctxt, name=self.name, code=self.code, fixtures=fixtures)


class HypocriteMock(object):
    """
    Represent a "mock" directive.  These directives describe functions
    to be mocked out.
    """

    TEMPLATE_VOID = 'mock-void.c'
    TEMPLATE = 'mock.c'

    def __init__(self, coord_range, name, return_type, args):
        """
        Initialize a ``HypocriteMock`` instance.

        :param coord_range: The range of coordinates associated with
                            the test in the hypocrite input file.
        :type coord_range: ``hypocrite.location.CoordinateRange``
        :param str name: The name of the function to mock.
        :param str return_type: The type of the function return value.
        :param list args: A list of ``HypoMockArg`` instances giving
                          the type and name of each function argument.
        """

        self.coord_range = coord_range
        self.name = name
        self.return_type = return_type
        self.args = args

    def render(self, hfile, ctxt):
        """
        Render a mock.  This uses a template to render the mock into
        actual output code.

        :param hfile: The hypocrite input file.
        :type hfile: ``HypocriteFile``
        :param ctxt: The render context.
        :type ctxt: ``hypocrite.template.RenderContext``
        """

        # First, pick the correct template and load it
        tmpl = template.Template.get_tmpl(
            self.TEMPLATE_VOID if self.return_type == 'void' else self.TEMPLATE
        )

        # Render the template
        tmpl.render(
            ctxt, name=self.name, return_type=self.return_type, args=self.args
        )


class Fixture(object):
    """
    Represent a "fixture" directive.  These directives describe
    fixtures that prepare the test environment prior to executing a
    given test.
    """

    TEMPLATE = 'fixture.c'

    def __init__(self, coord_range, name, return_type, code, teardown=None):
        """
        Initialize a ``Fixture`` instance.

        :param coord_range: The range of coordinates associated with
                            the test in the hypocrite input file.
        :type coord_range: ``hypocrite.location.CoordinateRange``
        :param str name: The base name of the fixture.
        :param str return_type: The type of the fixture return value.
                                May be ``None`` to indicate that the
                                fixture returns no values.
        :param code: The code of the fixture.
        :type code: ``hypocrite.linelist.LineList``
        :param teardown: The cleanup code for the fixture.  May be
                         ``None``.
        :type teardown: ``hypocrite.linelist.LineList``
        """

        self.coord_range = coord_range
        self.name = name
        self.return_type = return_type
        self.code = code
        self.teardown = teardown

    def render(self, hfile, ctxt):
        """
        Render a fixture.  This uses a template to render the fixture into
        actual output code.

        :param hfile: The hypocrite input file.
        :type hfile: ``HypocriteFile``
        :param ctxt: The render context.
        :type ctxt: ``hypocrite.template.RenderContext``
        """

        # Load the template
        tmpl = template.Template.get_tmpl(self.TEMPLATE)

        # Set up the correct arguments
        args = {
            'name': self.name,
            'return_type': self.return_type,
            'code': self.code,
        }
        if self.teardown:
            args['teardown'] = self.teardown

        # Render the template
        tmpl.render(ctxt, **args)


class HypoParser(perfile.PerFileParser):
    """
    Parser for hypocrite input files.
    """

    DIRECTIVES = {}


@HypoParser.directive(None, 'target')
def target_directive(values, start_coord, toks):
    """
    The ``%target`` directive.  Should contain a single TOK_STR token
    giving the name of the source file being tested.

    :param dict values: The values dictionary that the directive's
                        return value may be placed in.
    :param start_coord: The coordinates the directive started at.
    :type start_coord: ``hypocrite.location.Coordinate``
    :param list toks: A list of tokens.

    :returns: A ``None`` value to indicate no further processing is
              necessary.

    :raises hypocrite.perfile.ParseException:
        An error occurred while parsing the directive.
    """

    # Make sure the token list is correct
    if len(toks) != 1 or toks[0].type_ != perfile.TOK_STR or not toks[0].value:
        raise perfile.ParseException(
            'Invalid %%file directive at %s' % start_coord
        )

    # Save the target file
    values['target'] = toks[0].value

    return None


@HypoParser.directive(lambda: [], 'preamble')
class PreambleDirective(object):
    """
    The ``%preamble`` directive.  This is a multi-line directive that
    provides preamble code to include at the top of the generated test
    file.  Should contain a single TOK_CHAR token with the value '{'.
    Will be ended by a '%}' directive, which must appear at the
    beginning of a line.
    """

    def __init__(self, values, start_coord, toks):
        """
        Initialize a ``PreambleDirective`` instance.

        :param dict values: The values dictionary that the directive's
                            return value may be placed in.
        :param start_coord: The coordinates the directive started at.
        :type start_coord: ``hypocrite.location.Coordinate``
        :param list toks: A list of tokens.

        :raises hypocrite.perfile.ParseException:
            An error occurred while parsing the directive.
        """

        # Make sure the token list is correct
        if len(toks) != 1 or toks[0] != (perfile.TOK_CHAR, '{'):
            raise perfile.ParseException(
                'Invalid %%preamble directive at %s' % start_coord
            )

        # Save the gunk we need for __call__()
        self.values = values
        self.start_coord = start_coord

    def __call__(self, end_coord, buf, toks):
        """
        Called once processing of the directive is complete.

        :param end_coord: The coordinates at which the directive
                          processing completed.
        :type end_coord: ``hypocrite.location.Coordinate``
        :param list buf: A list of lines, including trailing newlines,
                         enclosed within the directive.
        :param list toks: A list of tokens.  Will be ``None`` if the
                          directive was closed by the end of file.

        :returns: A ``None`` value to indicate no further processing
                  is necessary.

        :raises hypocrite.perfile.ParseException:
            An error occurred while parsing the directive.
        """

        # Check for errors
        if toks is None:
            raise perfile.ParseException(
                'Unclosed %%preamble directive at end of file; '
                'starts at %s' % self.start_coord
            )
        elif len(toks) != 0:
            raise perfile.ParseException(
                'Invalid end of %%preamble directive at %s' % end_coord
            )

        # Update the preamble data
        self.values['preamble'].append(Preamble(
            self.start_coord - end_coord, buf
        ))

        return None


# Delimiters for type extraction for mocks
_mock_type_delims = {
    (perfile.TOK_CHAR, '('), (perfile.TOK_CHAR, ','), (perfile.TOK_CHAR, ')')
}


@HypoParser.directive(lambda: {}, key='mocks')
def mock(values, start_coord, toks):
    """
    The ``%mock`` directive.  Should contain a sequence of tokens
    declaring a function to be mocked, excluding any trailing
    semicolon (';').

    :param dict values: The values dictionary that the directive's
                        return value may be placed in.
    :param start_coord: The coordinates the directive started at.
    :type start_coord: ``hypocrite.location.Coordinate``
    :param list toks: A list of tokens.

    :returns: A ``None`` value to indicate no further processing is
              necessary.

    :raises hypocrite.perfile.ParseException:
        An error occurred while parsing the directive.
    """

    # Initialize the type iterator
    type_iter = _extract_type(toks, _mock_type_delims)

    # First, have to collect the return type and function name
    try:
        type_, name, delim = six.next(type_iter)
    except StopIteration:  # pragma: no cover
        # Shouldn't ever actually happen
        raise perfile.ParseException(
            'Invalid %%mock directive at %s' % start_coord
        )

    # Make sure the tokens make sense
    if (not type_ or name.type_ != perfile.TOK_WORD or not name.value or
            delim != (perfile.TOK_CHAR, '(')):
        raise perfile.ParseException(
            'Invalid %%mock directive at %s' % start_coord
        )

    # Initialize the mock information
    func_name = name.value
    return_type = _make_type(type_, 'mock', start_coord)
    args = []

    # Extract argument information
    end_expected = False
    for type_, name, delim in type_iter:
        # Were we expecting the end of the directive?
        if end_expected:
            if type_ or name or delim:
                raise perfile.ParseException(
                    'Unexpected tokens after %%mock directive at %s' %
                    start_coord
                )

            # Just here to exhaust the iterator for coverage
            continue  # pragma: no cover

        # OK, was it the end of the directive?
        elif not delim:
            raise perfile.ParseException(
                'Premature end of arguments in %%mock directive at %s' %
                start_coord
            )

        # Found the closing parenthesis
        elif delim == (perfile.TOK_CHAR, ')'):
            end_expected = True

            # Handles the case of 'void foo()' and 'void foo(void)'
            if not args and ((not type_ and not name) or
                             (not type_ and
                              name == (perfile.TOK_WORD, 'void'))):
                continue

        # Sanity-check the argument
        if (not type_ or
                not name or name.type_ != perfile.TOK_WORD or not name.value or
                delim == (perfile.TOK_CHAR, '(')):
            raise perfile.ParseException(
                'Invalid %%mock directive at %s' % start_coord
            )

        # Save the argument
        args.append(
            HypoMockArg(_make_type(type_, 'mock', start_coord), name.value)
        )

    # Construct and save the mock
    values['mocks'][func_name] = HypocriteMock(
        start_coord - start_coord, func_name, return_type, args
    )


@HypoParser.directive(collections.OrderedDict, 'test', 'tests')
class TestDirective(object):
    """
    The ``%test`` directive.  This is a multi-line directive that
    describes a single test to be included in the generated test file.
    Should contain a TOK_WORD token giving the name of the test,
    followed by a TOK_CHAR token with the value '{'.  Will be ended by
    a '%}' directive, which must appear at the beginning of a line.
    """

    def __init__(self, values, start_coord, toks):
        """
        Initialize a ``TestDirective`` instance.

        :param dict values: The values dictionary that the directive's
                            return value may be placed in.
        :param start_coord: The coordinates the directive started at.
        :type start_coord: ``hypocrite.location.Coordinate``
        :param list toks: A list of tokens.

        :raises hypocrite.perfile.ParseException:
            An error occurred while parsing the directive.
        """

        # Make sure the token list is correct
        if (len(toks) < 2 or toks[0].type_ != perfile.TOK_WORD or
                not toks[0].value or toks[-1] != (perfile.TOK_CHAR, '{')):
            raise perfile.ParseException(
                'Invalid %%test directive at %s' % start_coord
            )

        # Save the gunk we need for __call__()
        self.name = toks[0].value
        self.fixtures = []
        self.values = values
        self.start_coord = start_coord

        # Extract the optional fixtures
        if len(toks) > 2:
            if (toks[1] != (perfile.TOK_CHAR, '(') or
                    toks[-2] != (perfile.TOK_CHAR, ')')):
                raise perfile.ParseException(
                    'Invalid %%test directive at %s' % start_coord
                )

            for fix_toks in perfile.split_toks(toks[2:-2],
                                               {(perfile.TOK_CHAR, ',')}):
                # Sanity-check the tokens
                if len(fix_toks) < 1 or len(fix_toks) > 2:
                    raise perfile.ParseException(
                        'Invalid fixture specification in %%test directive '
                        'at %s' % start_coord
                    )

                # Determine if it's an injectable
                inject = True
                if fix_toks[0] == (perfile.TOK_CHAR, '!'):
                    inject = False
                    fix_toks.pop(0)

                # Determine the fixture name
                if (len(fix_toks) != 1 or
                        fix_toks[0].type_ != perfile.TOK_WORD or
                        not fix_toks[0].value):
                    raise perfile.ParseException(
                        'Invalid fixture specification in %%test directive '
                        'at %s' % start_coord
                    )

                # Add the fixture injection
                self.fixtures.append(HypoFixtureInjection(
                    fix_toks[0].value, inject
                ))

    def __call__(self, end_coord, buf, toks):
        """
        Called once processing of the directive is complete.

        :param end_coord: The coordinates at which the directive
                          processing completed.
        :type end_coord: ``hypocrite.location.Coordinate``
        :param list buf: A list of lines, including trailing newlines,
                         enclosed within the directive.
        :param list toks: A list of tokens.  Will be ``None`` if the
                          directive was closed by the end of file.

        :returns: A ``None`` value to indicate no further processing
                  is necessary.

        :raises hypocrite.perfile.ParseException:
            An error occurred while parsing the directive.
        """

        # Check for errors
        if toks is None:
            raise perfile.ParseException(
                'Unclosed %%test directive at end of file; starts at %s' %
                self.start_coord
            )
        elif len(toks) != 0:
            raise perfile.ParseException(
                'Invalid end of %%test directive at %s' % end_coord
            )

        # Save the test data
        self.values['tests'][self.name] = HypocriteTest(
            self.start_coord - end_coord, self.name, buf, self.fixtures
        )

        return None


@HypoParser.directive(lambda: {}, 'fixture', 'fixtures')
class FixtureDirective(object):
    """
    The ``%fixture`` directive.  This is a multi-line directive that
    describes a named fixture to execute before a test.  The directive
    may be followed by another multiline directive to provide cleanup
    code.
    """

    def __init__(self, values, start_coord, toks):
        """
        Initialize a ``FixtureDirective`` instance.

        :param dict values: The values dictionary that the directive's
                            return value may be placed in.
        :param start_coord: The coordinates the directive started at.
        :type start_coord: ``hypocrite.location.Coordinate``
        :param list toks: A list of tokens.

        :raises hypocrite.perfile.ParseException:
            An error occurred while parsing the directive.
        """

        # Parse the directive
        end_expected = False
        for type_, name, delim in _extract_type(toks,
                                                {(perfile.TOK_CHAR, '{')}):
            # Were we expecting the end of the directive?
            if end_expected:
                if type_ or name or delim:
                    raise perfile.ParseException(
                        'Unexpected tokens after %%fixture directive at %s' %
                        start_coord
                    )

                # Just here to exhaust the iterator for coverage
                continue  # pragma: no cover

            # OK, was it the end of the directive?
            elif not delim:
                raise perfile.ParseException(
                    'Premature end of arguments in %%fixture directive at %s' %
                    start_coord
                )

            # Found the open brace
            end_expected = True

            # Sanity-check the name token
            if not name or name.type_ != perfile.TOK_WORD or not name.value:
                raise perfile.ParseException(
                    'Invalid %%fixture directive at %s' % start_coord
                )

            # Save the fixture's type and name
            self.name = name.value
            self.type_ = (
                None if not type_ or type_ == [(perfile.TOK_WORD, 'void')]
                else _make_type(type_, 'fixture', start_coord)
            )
            self.values = values
            self.start_coord = start_coord
            self.block_start = start_coord

    def __call__(self, end_coord, buf, toks):
        """
        Called once processing of the directive is complete.

        :param end_coord: The coordinates at which the directive
                          processing completed.
        :type end_coord: ``hypocrite.location.Coordinate``
        :param list buf: A list of lines, including trailing newlines,
                         enclosed within the directive.
        :param list toks: A list of tokens.  Will be ``None`` if the
                          directive was closed by the end of file.

        :returns: A ``None`` value to indicate no further processing
                  is necessary, or a callable to collect the remaining
                  lines.

        :raises hypocrite.perfile.ParseException:
            An error occurred while parsing the directive.
        """

        # Check for errors
        if toks is None:
            raise perfile.ParseException(
                'Unclosed %%fixture directive at end of file; starts at %s' %
                self.block_start
            )
        elif (len(toks) != 0 and
              toks != [(perfile.TOK_WORD, 'teardown'),
                       (perfile.TOK_CHAR, '{')]):
            raise perfile.ParseException(
                'Invalid %%teardown directive at %s' % end_coord
            )

        # If we have a teardown clause, save the code clause and chain
        if toks:
            self.code = buf
            self.block_start = end_coord  # update to start of teardown
            return self.teardown

        # Create the fixture
        self.values['fixtures'][self.name] = Fixture(
            self.start_coord - end_coord, self.name, self.type_, buf
        )

        return None

    def teardown(self, end_coord, buf, toks):
        """
        Called once processing of the teardown directive is complete.

        :param end_coord: The coordinates at which the directive
                          processing completed.
        :type end_coord: ``hypocrite.location.Coordinate``
        :param list buf: A list of lines, including trailing newlines,
                         enclosed within the directive.
        :param list toks: A list of tokens.  Will be ``None`` if the
                          directive was closed by the end of file.

        :returns: A ``None`` value to indicate no further processing
                  is necessary.

        :raises hypocrite.perfile.ParseException:
            An error occurred while parsing the directive.
        """

        # Check for errors
        if toks is None:
            raise perfile.ParseException(
                'Unclosed %%teardown directive at end of file; starts at %s' %
                self.block_start
            )
        elif len(toks) != 0:
            raise perfile.ParseException(
                'Invalid end of %%teardown directive at %s' % end_coord
            )

        # Create the fixture
        self.values['fixtures'][self.name] = Fixture(
            self.start_coord - end_coord, self.name, self.type_, self.code, buf
        )

        return None


class HypoFile(object):
    """
    Represent a hypocrite input file.  These files consist of a
    sequence of comments (both C-style "/* */" and C++-style "//"
    comments are recognized) and directives, introduced by '%'
    characters.  Some directives are multi-line directives, delimited
    by an open '{' on the directive line and a '%}' on another line to
    indicate the end of the directive contents.  Directive lines may
    be continued to the next line by ending them with a '\\'
    character.
    """

    TEMPLATE = 'master.c'

    @classmethod
    def parse(cls, path):
        """
        Parse a file into a ``HypoFile`` instance.

        :param str path: The path to the hypocrite input file.

        :returns: An initialized hypocrite file representation.
        :rtype: ``HypoFile``

        :raises hypocrite.perfile.ParseException:
            An error occurred while parsing the input file.
        """

        # Grab a parser instance
        parser = HypoParser()

        # Parse the input file
        with open(path, 'rU') as stream:
            values = parser.parse(stream, path)

        return cls(path, **values)

    def __init__(self, path, target, preamble, tests, mocks, fixtures):
        """
        Initialize a ``HypoFile`` instance.

        :param str path: The path to the hypocrite input file.
        :param str target: The target file being tested.  This will be
                           included by the generated test file.
        :param list preamble: A list of preambles (instances of
                              ``Preamble``) listing preambles to
                              include in the generated test file.
        :param dict tests: A dictionary (probably a
                           ``collections.OrderedDict``) mapping test
                           names to test descriptions (instances of
                           ``HypocriteTest``).
        :param dict mocks: A dictionary mapping the names of C
                           functions to mock to descriptions of those
                           mocks (instances of ``HypocriteMock``).
        :param dict fixtures: A dictionary mapping the names of test
                              fixtures to descriptions of those
                              fixtures (instances of ``Fixture``).
        """

        self.path = path
        self.target = target
        self.preamble = preamble
        self.tests = tests
        self.mocks = mocks
        self.fixtures = fixtures

    def render(self, test_fname):
        """
        Render the ``HypoFile`` instance into an output file.

        :param str test_fname: The base name of the test file.

        :returns: A list of lines to be emitted to the output file.
        :rtype: ``hypocrite.linelist.LineList``
        """

        # First, set up a render context
        ctxt = template.RenderContext()

        # Now render all the elements, starting with the preamble
        for preamble in self.preamble:
            preamble.render(self, ctxt)
        for test in self.tests.values():
            test.render(self, ctxt)
        for _name, mock in sorted(self.mocks.items(), key=lambda x: x[0]):
            mock.render(self, ctxt)
        for _name, fix in sorted(self.fixtures.items(), key=lambda x: x[0]):
            fix.render(self, ctxt)

        # Grab the master template
        tmpl = template.Template.get_tmpl(self.TEMPLATE)

        # Render it and return the code
        return tmpl.render(
            ctxt,
            source=os.path.basename(self.path),
            target=self.target,
            test_fname=test_fname,
        )
