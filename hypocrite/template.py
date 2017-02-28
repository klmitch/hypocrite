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
import io
import re

import jinja2
import pkg_resources
import six

from hypocrite import linelist
from hypocrite import perfile

# Regular expression for section template rendering
SUBST_RE = re.compile(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}')

# Location of templates
TEMPLATES = 'templates/%s'


class InsertSection(object):
    """
    Represent an "insert section" directive.  These directives, along
    with "literal" directives, are processed during the ``render()``
    phase of template realization.
    """

    def __init__(self, coord_range, section):
        """
        Initialize an ``InsertSection`` instance.

        :param coord_range: The range of coordinates associated with
                            the directive in the template.
        :type coord_range: ``hypocrite.location.CoordinateRange``
        :param str section: The name of the section to insert.
        """

        self.coord_range = coord_range
        self.section = section

    def render(self, ctxt):
        """
        Render an ``InsertSection`` instance.

        :param ctxt: A render context containing the sections.
        :type ctxt: ``RenderContext``

        :returns: The relevant lines to insert into the rendered file.
        :rtype: ``hypocrite.linelist.LineList``
        """

        return ctxt.sections[self.section]


class Literal(object):
    """
    Represent a "literal" directive.  These directives, along with
    "insert section" directives, are processed during the ``render()``
    phase of template realization.
    """

    def __init__(self, coord_range, code):
        """
        Initialize a ``Literal`` instance.

        :param coord_range: The range of coordinates associated with
                            the directive in the template.
        :type coord_range: ``hypocrite.location.CoordinateRange``
        :param code: The literal code to insert.
        :type code: ``hypocrite.linelist.LineList``
        """

        self.coord_range = coord_range
        self.code = code

    def render(self, ctxt):
        """
        Render a ``Literal`` instance.

        :param ctxt: A render context.
        :type ctxt: ``RenderContext``

        :returns: The relevant literal lines to insert into the
                  rendered file.
        :rtype: ``hypocrite.linelist.LineList``
        """

        return self.code


class Define(object):
    """
    Represent a "define" directive.  These directives contain Jinja
    templates that are rendered and later inserted into ``Section``
    templates.  These are processed during the ``prepare()`` phase of
    template realization.
    """

    def __init__(self, coord_range, name, contents):
        """
        Initialize a ``Define`` instance.

        :param coord_range: The range of coordinates associated with
                            the directive in the template.
        :type coord_range: ``hypocrite.location.CoordinateRange``
        :param str name: The name of the variable that the results of
                         rendering the Jinja template will be stored
                         in.
        :param contents: The contents.  This must be a Jinja template.
        :type contents: ``hypocrite.linelist.LineList``
        """

        self.coord_range = coord_range
        self.name = name
        self.contents = contents

        # Parse the Jinja template
        self.template = jinja2.Template('\n'.join(contents))

    def render(self, kwargs):
        """
        Render a ``Define`` instance.

        :param dict kwargs: The arguments to use while rendering the
                            Jinja template.

        :returns: The rendered Jinja template.
        :rtype: ``str``
        """

        return self.template.render(kwargs)


class Section(object):
    """
    Represent a "section" directive.  These directives contain
    templates that are rendered, then stored in a named section of the
    render context.  These are processed during the ``prepare()``
    phase of template realization.
    """

    def __init__(self, coord_range, name, requires, contents):
        """
        Initialize a ``Section`` instance.

        :param coord_range: The range of coordinates associated with
                            the directive in the template.
        :type coord_range: ``hypocrite.location.CoordinateRange``
        :param str name: The name of the section that the results of
                         rendering the template will be stored in.
        :param set requires: A (possibly empty) set of variable names
                             which must have values in order to render
                             the template.
        :param contents: The contents.  This must be C code containing
                         either plain expandos (variable names
                         surrounded by ``'{{'`` and ``'}}'``) or lines
                         containing the pseudo-preprocessor
                         instruction '#replace'.  Note that these are
                         *not* Jinja templates, due to the requirement
                         to properly generate location data.
        :type contents: ``hypocrite.linelist.LineList``
        """

        self.coord_range = coord_range
        self.name = name
        self.requires = requires
        self.contents = contents

    def render(self, kwargs):
        """
        Render a ``Section`` instance.

        :param dict kwargs: The arguments to use while rendering the
                            section template.

        :returns: Either ``None`` or an instance of
                  ``hypocrite.linelist.LineList`` containing the lines
                  to add to the designated section.
        """

        if self.requires - set(kwargs):
            # Missing variables, don't render it
            return None

        result = linelist.LineList()

        for coord, text in self.contents.iter_coord():
            if text.startswith('#replace'):
                # Multi-line replacement
                var = text.split()[1]
                for line in kwargs[var]:
                    result.append(line)
            else:
                # Make any necessary substitutions
                line = SUBST_RE.sub(lambda x: kwargs[x.group(1)], text)
                result.append(line, coord)

        return result


class TemplateParser(perfile.PerFileParser):
    """
    Parser for hypocrite template files.
    """

    DIRECTIVES = {}


@TemplateParser.directive(lambda: [], key='structure')
def insert(values, start_coord, toks):
    """
    The ``%insert`` directive.  Should contain a single TOK_WORD token
    giving the name of the section to insert into the file's
    structure.

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
    if (len(toks) != 1 or toks[0].type_ != perfile.TOK_WORD or
            not toks[0].value):
        raise perfile.ParseException(
            'Invalid %%insert directive at %s' % start_coord
        )

    # Add an insert-section directive
    values['structure'].append(InsertSection(
        start_coord - start_coord, toks[0].value
    ))

    return None


@TemplateParser.directive(name='literal')
class LiteralDirective(object):
    """
    The ``%literal`` directive.  This is a multi-line directive that
    provides bare code which is inserted literally into the output.
    Should contain a single TOK_CHAR token with the value '{'.  Will
    be ended by a '%}' directive, which must appear at the beginning
    of a line.
    """

    def __init__(self, values, start_coord, toks):
        """
        Initialize a ``LiteralDirective`` instance.

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
                'Invalid %%literal directive at %s' % start_coord
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
                'Unclosed %%literal directive at end of file; starts at %s' %
                self.start_coord
            )
        elif len(toks) != 0:
            raise perfile.ParseException(
                'Invalid end of %%literal directive at %s' % end_coord
            )

        # Add a literal directive
        self.values['structure'].append(Literal(
            self.start_coord - end_coord, buf
        ))

        return None


@TemplateParser.directive(collections.OrderedDict, 'define', 'defines')
class DefineDirective(object):
    """
    The ``%define`` directive.  This is a multi-line directive that
    provides a Jinja template, which is rendered into a variable that
    can be substituted into a ``%section`` template.  Should contain a
    TOK_WORD token giving the name of the variable to create from the
    rendered template, followed by a TOK_CHAR token with the value
    '{'.  Will be ended by a '%}' directive, which must appear at the
    beginning of a line.
    """

    def __init__(self, values, start_coord, toks):
        """
        Initialize a ``DefineDirective`` instance.

        :param dict values: The values dictionary that the directive's
                            return value may be placed in.
        :param start_coord: The coordinates the directive started at.
        :type start_coord: ``hypocrite.location.Coordinate``
        :param list toks: A list of tokens.

        :raises hypocrite.perfile.ParseException:
            An error occurred while parsing the directive.
        """

        # Make sure the token list is correct
        if (len(toks) != 2 or toks[0].type_ != perfile.TOK_WORD or
                not toks[0].value or toks[1] != (perfile.TOK_CHAR, '{')):
            raise perfile.ParseException(
                'Invalid %%define directive at %s' % start_coord
            )

        # Save the gunk we need for __call__()
        self.name = toks[0].value
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
                'Unclosed %%define directive at end of file; starts at %s' %
                self.start_coord
            )
        elif len(toks) != 0:
            raise perfile.ParseException(
                'Invalid end of %%define directive at %s' % end_coord
            )

        # Save the define
        self.values['defines'][self.name] = Define(
            self.start_coord - end_coord, self.name, buf
        )

        return None


@TemplateParser.directive(lambda: {}, 'section', 'sections')
class SectionDirective(object):
    """
    The ``%section`` directive.  This is a multi-line directive that
    provides template code that will be added to a particular section
    of the result file.  Variables surrounded with '{{' and '}}' will
    be inserted directly, as with Jinja (though the advanced features,
    such as filters, are not recognized).  Lines beginning with
    ``#replace`` work similarly, but for multi-line substitutions.
    Should contain a TOK_WORD token giving the name of the section to
    be added, and should end with a TOK_CHAR token with the value '{'.
    Additional comma-separated TOK_WORD tokens, surrounded by '(' and
    ')' tokens, indicate variables that must be set for the section to
    be rendered.  Will be ended by a '%}' directive, which must appear
    at the beginning of a line.
    """

    def __init__(self, values, start_coord, toks):
        """
        Initialize a ``SectionDirective`` instance.

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
                'Invalid %%section directive at %s' % start_coord
            )

        # Check for requirements
        requires = set()
        if len(toks) > 2:
            if (len(toks) < 4 or toks[1] != (perfile.TOK_CHAR, '(') or
                    toks[-2] != (perfile.TOK_CHAR, ')')):
                raise perfile.ParseException(
                    'Invalid %%section directive at %s' % start_coord
                )

            for requirement in perfile.split_toks(toks[2:-2],
                                                  {(perfile.TOK_CHAR, ',')}):
                if (len(requirement) != 1 or
                        requirement[0].type_ != perfile.TOK_WORD or
                        not requirement[0].value):
                    raise perfile.ParseException(
                        'Invalid %%section directive at %s' % start_coord
                    )

                requires.add(requirement[0].value)

        # Save the gunk we need for __call__()
        self.name = toks[0].value
        self.requires = requires
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
                'Unclosed %%section directive at end of file; starts at %s' %
                self.start_coord
            )
        elif len(toks) != 0:
            raise perfile.ParseException(
                'Invalid end of %%section directive at %s' % end_coord
            )

        # Save the section
        self.values['sections'][self.name] = Section(
            self.start_coord - end_coord, self.name, self.requires, buf
        )

        return None


class RenderContext(object):
    """
    A context to use while rendering the templates.  Instances of this
    class accumulate the output, as well as section data to be
    inserted into the output.
    """

    def __init__(self):
        """
        Initialize a ``RenderContext`` instance.
        """

        self.output = linelist.LineList()
        self.sections = collections.defaultdict(linelist.LineList)


class Template(object):
    """
    Represent a template to be rendered.
    """

    # Cache of templates, so they don't have to be loaded over and
    # over
    _tmpl_cache = {}

    @classmethod
    def get_tmpl(cls, name):
        """
        Retrieve a template with the given name.

        :param str name: The name of the template.  Must exist in the
                         templates directory.

        :returns: A template.
        :rtype: ``Template``
        """

        # Do we need to suck it in?
        if name not in cls._tmpl_cache:
            # Grab the resource stream
            resource_name = TEMPLATES % name
            raw_stream = pkg_resources.resource_stream(
                'hypocrite', resource_name
            )

            # Paper over a py2/py3 mismatch
            if six.PY2 and isinstance(raw_stream, file):  # pragma: no cover
                raw_stream = io.BufferedReader(_ReadableWrapper(raw_stream))

            # We need a text stream with universal newlines
            stream = io.TextIOWrapper(raw_stream)

            # Initialize a parser and parse the stream
            parser = TemplateParser()
            values = parser.parse(stream, name)

            # Create and cache the template
            cls._tmpl_cache[name] = cls(name, **values)

        return cls._tmpl_cache[name]

    def __init__(self, name, structure, defines, sections):
        """
        Initialize a ``Template`` instance.

        :param str name: The name of the template.
        :param list structure: A list of structure elements, instances
                               of ``InsertSection`` and ``Literal``
                               that describe how to construct the
                               output file.
        :param dict defines: A dictionary (probably a
                             ``collections.OrderedDict``) mapping
                             variable names to Jinja templates that
                             should be rendered to produce values for
                             those variables.  The variables are then
                             expected to be used in rendering
                             sections.
        :param dict sections: A dictionary mapping section names to a
                              description of the section template.
                              The rendered sections may be inserted
                              into the output based on
                              ``InsertSection`` instances in
                              ``structure``.
        """

        self.name = name
        self.structure = structure
        self.defines = defines
        self.sections = sections

    def render(self, ctxt, **kwargs):
        """
        Render a ``Template`` instance.

        :param ctxt: A render context.
        :type ctxt: ``RenderContext``
        :param dict kwargs: A dictionary of arguments to use while
                            rendering ``Define`` and ``Section``
                            instances.

        :returns: The ``hypocrite.linelist.LineList`` containing the
                  output from ``ctxt``.  This is for convenience.
        """

        # First, realize all the defines
        for name, define in self.defines.items():
            result = define.render(kwargs)

            # Split multi-line defines
            if '\n' in result:
                result = result.split('\n')
                if not result[-1]:
                    # Eliminate the trailing blank line
                    result.pop()

            # Add the result back to the keyword arguments
            kwargs[name] = result

        # Next, render all the sections
        for name, section in self.sections.items():
            result = section.render(kwargs)
            if result:
                ctxt.sections[name] += result

        # Finally, render the output
        for elem in self.structure:
            ctxt.output += elem.render(ctxt)

        # For convenience
        return ctxt.output


if six.PY2:  # pragma: no cover
    class _ReadableWrapper(object):
        """
        In Python 2, the standard ``file`` object (which does *not* exist
        in Python 3) cannot be directly wrapped with
        ``io.TextIOWrapper``.  That would be fine, except that
        ``pkg_resources.resource_stream()`` can return a ``file``
        object in binary mode, and we need text mode with universal
        newlines.  So, this class provides an extremely thin wrapper
        around ``file`` objects, providing enough of an interface for
        the object to be wrapped in ``io.BufferedReader``, which in
        turn provides the facilities needed by ``io.TextIOWrapper``.

        This class (and indeed the ``io.BufferedReader`` wrapper) is
        unneeded in Python 3, as ``io.TextIOWrapper`` can directly
        wrap the object returned by ``open()`` (which, in Python 3, is
        in fact an ``io.BufferedReader`` anyway).
        """

        def __init__(self, raw):
            """
            Initialize a ``_ReadableWrapper`` instance.

            :param raw: The raw ``file`` object.
            """

            self._raw = raw

        def readable(self):
            """
            Determine if the stream is readable.

            :returns: A ``True`` value to indicate that the stream is
                      readable.
            """

            return True

        def writable(self):
            """
            Determine if the stream is writable.

            :returns: A ``False`` value to indicate that the stream is
                      not writable.
            """

            return False

        def seekable(self):
            """
            Determine if the stream is seekable.

            :returns: A ``True`` value to indicate that the stream is
                      seekable.
            """

            return True

        def __getattr__(self, name):
            """
            Retrieve an attribute with a given name.  This delegates to the
            underlying raw object.

            :param str name: The name of the attribute to retrieve.

            :returns: The value of the desired attribute.
            """

            return getattr(self._raw, name)
