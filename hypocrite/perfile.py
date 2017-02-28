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

import abc
import collections

import six

from hypocrite import location
from hypocrite import linelist

_unset = object()

# Represent a token
Token = collections.namedtuple('Token', ['type_', 'value'])

# Known token types
TOK_WORD = 'word'
TOK_CHAR = 'char'
TOK_STR = 'str'


class Continue(Exception):
    """
    A specialized exception indicating that the loop should be
    continued.
    """

    pass


class ParseException(Exception):
    """
    Exceptions related to hypocrite, such as parse errors.
    """

    pass


def split_toks(toks, delims, include_delim=False):
    """
    Helper to split a list of tokens on a specific set of delimiters,
    similar to ``str.split()``.

    :param list toks: The list of tokens to split.
    :param set delims: The delimiters to use to split the tokens.
    :param bool include_delim: If ``True``, then the value yielded
                               will be a 2-element tuple, with the
                               second element containing the
                               delimiter.

    :returns: An iterator that yields lists of tuples.
    """

    # Stack of tokens seen so far
    stack = []

    for current in toks:
        # Have we encountered a delimiter?
        if current in delims:
            # Yield the value, then reset the stack and keep going
            yield (stack, current) if include_delim else stack
            stack = []
            continue

        # Add the token to the stack
        stack.append(current)

    # Yield any outstanding tokens
    yield (stack, None) if include_delim else stack


class Directive(object):
    """
    Wrap a directive declaration.  Directives have a name, a value
    key, an initial value for that key, and a callable implementing
    the directive's behavior.
    """

    def __init__(self, directive, value, init, impl):
        """
        Initialize a ``directive`` instance.

        :param str directive: The directive, e.g., 'file' for a
                              ``%file`` directive.
        :param str value: The value key.  This is where the value
                          produced by the directive is to be stored.
                          May be ``None`` if the directive produces no
                          independent values of its own.
        :param init: The initial value for the directive value.  If it
                     is ``_unset``, the directive produces no
                     independent values of its own; if it is callable,
                     it will be called with no arguments and the
                     return value will be the initial value;
                     otherwise, it is used verbatim.  Be careful to
                     use a callable for mutable objects such as
                     dictionaries.
        :param impl: A callable implementing the directive.  This
                     callable is expected to take the variables
                     ``values`` (a dictionary), ``start_coord`` (the
                     coordinates the directive started at), and
                     ``toks`` (a list of tokens).  The callable is
                     expected to return ``None`` or another callable
                     accepting ``end_coord`` (the coordinates the
                     directive ended at), ``buf`` (a list of lines),
                     and ``toks`` (a list of tokens), which may also
                     return either ``None`` or another callable.
        """

        self.directive = directive
        self.value = value
        self.init = init
        self.impl = impl

    def __call__(self, values, start_coord, toks):
        """
        Call the implementation of the directive.

        :param dict values: The values dictionary that the directive's
                            return value may be placed in.
        :param start_coord: The coordinates the directive started at.
        :type start_coord: ``hypocrite.location.Coordinate``

        :param list toks: A list of tokens.

        :returns: Either ``None`` or another callable accepting
                  ``end_coord`` (the coordinates the directive ended
                  at), ``buf`` (a list of lines), and ``toks`` (a list
                  of tokens), which may also return either ``None`` or
                  another similar callable.
        """

        return self.impl(values, start_coord, toks)

    def initial(self):
        """
        Return the initial value to store for the directive.
        """

        return self.init() if callable(self.init) else self.init


@six.add_metaclass(abc.ABCMeta)
class PerFileParser(object):
    """
    Track the state of parsing a percent-directive file.
    """

    @abc.abstractproperty
    def DIRECTIVES(self):
        """
        A class-level dictionary.  This should be initialized to an empty
        dictionary, and will be filled in using the ``@directive()``
        class method.
        """

        pass  # pragma: no cover

    @staticmethod
    def _tokenize(text, coord):
        """
        Given directive text, not including the leading '%' character,
        decompose it into a sequence of tokens.

        :param str text: The text to tokenize.
        :param coord: The coordinates of the line.
        :type coord: ``hypocrite.location.Coordinate``

        :returns: An iterator over the sequence of tokens in the text.
        """

        # Tokenizing state and initialized buffer
        state = None
        buf = ''

        # Step through the text a character at a time
        for c in text:
            # None state indicates we're handling whitespace (which is
            # ignored)
            if state is None:
                if c.isspace():
                    # More whitespace
                    pass
                elif c == '"':
                    # Introduce a string token (delimited by
                    # double-quotes)
                    state = TOK_STR
                    buf = ''
                elif c == '_' or c.isalpha():
                    # Found a word
                    state = TOK_WORD
                    buf = c
                else:
                    # Some other character; yield a CHAR token
                    yield Token(TOK_CHAR, c)

            elif state == TOK_STR:
                # Processing a string.  Note that escapes are NOT honored
                if c == '"':
                    # Found the end of the string!
                    yield Token(state, buf)
                    state = None
                else:
                    # Add the character to the buffer
                    buf += c

            elif c.isspace():
                # Plain old whitespace, ending a WORD token
                yield Token(state, buf)
                state = None

            else:
                # Can't be in any other state
                assert state == TOK_WORD

                if c == '_' or c.isalnum():
                    # Still a WORD token
                    buf += c
                else:
                    # Oh, end of the WORD token
                    yield Token(state, buf)
                    if c == '"':
                        # WORD ended on a STR token
                        state = TOK_STR
                        buf = ''
                    else:
                        # Some other character
                        state = None
                        yield Token(TOK_CHAR, c)

        if state == TOK_STR:
            # Last STR token was missing a close quote!
            raise ParseException(
                'Unclosed string encountered at %s' % coord
            )
        elif state is not None:
            # Have a WORD pending in the buffer
            yield Token(state, buf)

    @classmethod
    def directive(cls, init=_unset, name=None, key=_unset):
        """
        Declare a directive.  This is a decorator that marks a function or
        class as implementing a directive.

        :param init: The initial value to store for the directive.  If
                     a callable, will be called with no arguments to
                     produce the initial value; use this when the
                     value should be initialized to mutable objects,
                     such as dictionaries.
        :param str name: The directive name.  This appears after the
                         ``%`` character to identify the directive.
                         If not provided, defaults to the name of the
                         class or function.
        :param str key: The value key the directive stores its data
                        under.  Defaults to ``name``.  May be set to
                        ``None`` to inhibit initializing the value.

        :returns: A function decorator.
        """

        def decorator(func):
            # Pick the directive and value key
            directive = name or func.__name__
            value = directive if key is _unset else key

            # Save the directive
            cls.DIRECTIVES[directive] = Directive(
                directive, value, init, func
            )

            return func

        # Return the decorator
        return decorator

    @classmethod
    def _values(cls):
        """
        Initialize a values dictionary for all directives.

        :returns: A dictionary of values.
        :rtype: ``dict``
        """

        return {
            directive.value: directive.initial()
            for directive in cls.DIRECTIVES.values()
            if directive.init is not _unset
        }

    def __init__(self):
        """
        Initialize a ``PerFileParser`` instance.
        """

        self._deferred = None
        self._buf = None
        self._comment_pfx = None
        self._continued = None
        self._start_coord = None
        self._lines = 0

    def _parse_directive(self, coord, line):
        """
        Parse a line looking for a directive.  This is the core parsing
        functionality.  This routine recognizes both C-style comments
        ("/* */") and one-line comments ("//"); the former are
        replaced with spaces anywhere they are encountered, while the
        latter are simply stripped from the line.  Line continuations,
        identified as backslashes ("\\") at the end of a line, are
        also recognized.

        :param coord: The coordinates of the line.
        :type coord: ``hypocrite.location.Coordinate``
        :param str line: The line to parse.

        :returns: A tuple of the line number the directive started on
                  (which, thanks to comments and continuations, may
                  not be the same as ``coord``) and a list of tokens
                  parsed from the directive line.

        :raises Continue:
            Indicates that further input is required.  This typically
            means the line was empty or that a C-style comment
            spanning multiple lines was encountered.

        :raises ParseException:
            An error occurred while parsing the input file.
        """

        # Handle any continuation
        if self._continued is not None:
            line = self._continued + ' ' + line
            self._continued = None

        # Handle any hanging comment
        if self._comment_pfx is not None:
            # Comment started above; does it end here?
            end = line.find('*/')
            if end < 0:
                # Nope
                raise Continue()

            # Comment has ended, pretend it was a space and reset
            # the comment state
            line = self._comment_pfx + ' ' + line[end + 2:]
            self._comment_pfx = None

        # Strip out any other comments on the line
        while True:
            # Does the line contain any comments?
            pos = [x for x in (line.find('/*'), line.find('//')) if x >= 0]
            if not pos:
                break

            # What's the first one?
            comment = min(pos)

            # Handle the simple case of a one-line comment
            if line[comment:comment + 2] == '//':
                line = line[:comment]

                # Can't be any more comments, so exit the comment
                # loop
                break

            # OK, a C-style comment; does it end on this line?
            end = line.find('*/', comment + 2)
            if end < 0:
                # Nope; can't continue until we have more
                self._comment_pfx = line[:comment]
                if self._start_coord is None:
                    self._start_coord = coord
                raise Continue()

            # Replace the comment with a space
            line = line[:comment] + ' ' + line[end + 2:]

            # Loop around for any more comments

        # Strip off remaining whitespace and skip empty lines
        line = line.strip()
        if not line:
            raise Continue()

        # If it has a continuation, process that
        if line[-1] == '\\':
            self._continued = line[:-1]
            if self._start_coord is None:
                self._start_coord = coord
            raise Continue()

        # Now we have a line; pick the correct line number
        if self._start_coord:
            coord = self._start_coord
            self._start_coord = None

        # It's supposed to be a directive, so check that it is
        if line[0] != '%':
            raise ParseException('Invalid directive at %s' % coord)

        # Tokenize the line and return the starting line number and
        # the tokens
        return coord, list(self._tokenize(line[1:], coord))

    def _parse_line(self, coord, line, values):
        """
        Parse a line.  This wraps the ``_parse_directive()`` routine,
        handling deferred processing.  Deferred processing allows
        directives to include content that spans multiple lines;
        examples include the ``%preamble`` and ``%test`` directives.

        :param coord: The coordinates of the line.
        :type coord: ``hypocrite.location.Coordinate``
        :param str line: The line to parse.
        :param dict values: The directive values being accumulated by
                            the parsing process.

        :raises Continue:
            Indicates that further input is required.  This typically
            means the line was empty or that a C-style comment
            spanning multiple lines was encountered.

        :raises ParseException:
            An error occurred while parsing the input file.
        """

        # Keep track of how many lines have been processed
        self._lines += 1

        # If we don't have a pending deferred callable, that means
        # we're looking for directives...
        if self._deferred is None:
            # Parse out a directive
            dir_coord, tokens = self._parse_directive(coord, line)

            # Is it a valid directive?
            if (not tokens or tokens[0].type_ != TOK_WORD or
                    tokens[0].value not in self.DIRECTIVES):
                raise ParseException(
                    'Invalid directive at %s' % dir_coord
                )

            # Process the directive
            self._deferred = self.DIRECTIVES[tokens[0].value](
                values, dir_coord, tokens[1:]
            )
            self._buf = linelist.LineList() if self._deferred else None

        # OK, we're accumulating lines looking for an end directive
        elif (self._comment_pfx is not None or
              self._continued is not None or line.lstrip().startswith('%')):
            # Parse out a directive
            dir_coord, tokens = self._parse_directive(coord, line)

            # Is it a close directive?
            if not tokens or tokens[0] != (TOK_CHAR, '}'):
                raise ParseException(
                    'Invalid directive at %s' % dir_coord
                )

            # Run the deferred callable
            self._deferred = self._deferred(dir_coord, self._buf, tokens[1:])
            self._buf = linelist.LineList() if self._deferred else None

        else:
            # Just accumulate another line
            self._buf.append(line[:-1] if line.endswith('\n') else line, coord)

    def parse(self, stream, path=None):
        """
        Parse a percent-directive file.

        :param stream: A stream, as opened with ``open()``.  The
                       stream should be opened in text mode with
                       universal newlines.
        :param str path: The path of the file being parsed.  If not
                         provided, ``stream.name`` will be used.

        :returns: A dictionary of values developed from parsing the
                  directives contained within the input file.

        :raises AttributeError:
            The provided ``stream`` has no ``name`` attribute and
            ``path`` was not provided.

        :raises ParseException:
            An error occurred while parsing the input file.
        """

        # Figure out the path
        if path is None:
            path = stream.name

        # Start with the initialized values
        values = self._values()

        # Parse the stream
        for lno, line in enumerate(stream):
            try:
                self._parse_line(
                    location.Coordinate(path, lno + 1), line, values
                )
            except Continue:
                # Special exception indicating an extended line
                continue

        # Was there a line continuation?
        if self._continued is not None:
            raise ParseException(
                'Trailing directive continuation at end of file; '
                'starts at %s' % self._start_coord
            )

        # Were we in the middle of a comment?
        if self._comment_pfx is not None:
            raise ParseException(
                'Unclosed comment at end of file; starts at %s' %
                self._start_coord
            )

        # How about the middle of a directive?
        if self._deferred:
            # Give the deferred routine a chance to complain
            self._deferred(
                location.Coordinate(path, self._lines), self._buf, None
            )

            # But complain anyway if it doesn't
            raise ParseException('Unclosed directive at end of file')

        return values
