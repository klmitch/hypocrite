import collections

import pytest

from hypocrite import linelist
from hypocrite import location
from hypocrite import perfile
from hypocrite import template


class TestInsertSection(object):
    def test_init(self):
        result = template.InsertSection('range', 'section')

        assert result.coord_range == 'range'
        assert result.section == 'section'

    def test_render(self, mocker):
        ctxt = mocker.Mock(sections={'section': 'value'})
        obj = template.InsertSection('range', 'section')

        result = obj.render(ctxt)

        assert result == 'value'


class TestLiteral(object):
    def test_init(self):
        result = template.Literal('range', 'code')

        assert result.coord_range == 'range'
        assert result.code == 'code'

    def test_render(self, mocker):
        obj = template.Literal('range', 'code')

        result = obj.render('ctxt')

        assert result == 'code'


class TestDefine(object):
    def test_init(self, mocker):
        mock_Template = mocker.patch.object(template.jinja2, 'Template')

        result = template.Define('range', 'name', ['line1', 'line2', 'line3'])

        assert result.coord_range == 'range'
        assert result.name == 'name'
        assert result.contents == ['line1', 'line2', 'line3']
        assert result.template == mock_Template.return_value
        mock_Template.assert_called_once_with('line1\nline2\nline3')

    def test_render_one_line(self, mocker):
        mock_Template = mocker.patch.object(template.jinja2, 'Template')
        tmpl = mock_Template.return_value
        tmpl.render.return_value = 'one line'
        obj = template.Define('range', 'name', ['line1', 'line2', 'line3'])

        result = obj.render({'a': 1, 'b': 2, 'c': 3})

        assert result == 'one line'
        tmpl.render.assert_called_once_with({'a': 1, 'b': 2, 'c': 3})

    def test_render_multi_line(self, mocker):
        mock_Template = mocker.patch.object(template.jinja2, 'Template')
        tmpl = mock_Template.return_value
        tmpl.render.return_value = 'one line\ntwo line'
        obj = template.Define('range', 'name', ['line1', 'line2', 'line3'])

        result = obj.render({'a': 1, 'b': 2, 'c': 3})

        assert result == ['one line', 'two line']
        tmpl.render.assert_called_once_with({'a': 1, 'b': 2, 'c': 3})

    def test_render_multi_line_no_empty(self, mocker):
        mock_Template = mocker.patch.object(template.jinja2, 'Template')
        tmpl = mock_Template.return_value
        tmpl.render.return_value = 'one line\ntwo line\n'
        obj = template.Define('range', 'name', ['line1', 'line2', 'line3'])

        result = obj.render({'a': 1, 'b': 2, 'c': 3})

        assert result == ['one line', 'two line']
        tmpl.render.assert_called_once_with({'a': 1, 'b': 2, 'c': 3})


class TestSection(object):
    def test_init(self):
        result = template.Section('range', 'name', 'requires', 'contents')

        assert result.coord_range == 'range'
        assert result.name == 'name'
        assert result.requires == 'requires'
        assert result.contents == 'contents'

    def test_render_missing(self):
        obj = template.Section('range', 'name', {'a', 'b'}, 'contents')

        result = obj.render({'a': 1, 'c': 3})

        assert result is None

    def test_render_base(self):
        contents = linelist.LineList([
            'line1',
            'line2',
            '#replace foo',
            '#replace spam',
            '#replace llist',
            'line {{bar}} {{baz}} 4',
        ], 5)
        obj = template.Section('range', 'name', set(), contents)
        kwargs = {
            'foo': ['sub line1', 'sub line2'],
            'bar': 'baz',
            'baz': 'spam',
            'spam': 'one line',
            'llist': linelist.LineList([
                'l1',
                'l2',
                'l3',
            ], 1),
        }

        result = obj.render(kwargs)

        assert list(result.iter_coord()) == [
            (5, 'line1'),
            (6, 'line2'),
            (None, 'sub line1'),
            (None, 'sub line2'),
            (None, 'one line'),
            (1, 'l1'),
            (2, 'l2'),
            (3, 'l3'),
            (10, 'line baz spam 4'),
        ]


class TestInsertDirective(object):
    def test_initial(self):
        result = template.TemplateParser.DIRECTIVES['insert'].init()

        assert result == []

    def test_base(self, mocker):
        mock_InsertSection = mocker.patch.object(template, 'InsertSection')
        values = {'structure': []}
        coord = location.Coordinate('path', 23)
        toks = [perfile.Token(perfile.TOK_WORD, 'section')]

        result = template.insert(values, coord, toks)

        assert result is None
        assert values == {
            'structure': [mock_InsertSection.return_value],
        }
        mock_InsertSection.assert_called_once_with(
            location.CoordinateRange('path', 23, 23), 'section'
        )

    def test_too_many_toks(self, mocker):
        mock_InsertSection = mocker.patch.object(template, 'InsertSection')
        values = {'structure': []}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'section'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            template.insert(values, coord, toks)

        assert values == {'structure': []}
        assert not mock_InsertSection.called

    def test_empty_tok(self, mocker):
        mock_InsertSection = mocker.patch.object(template, 'InsertSection')
        values = {'structure': []}
        coord = location.Coordinate('path', 23)
        toks = [perfile.Token(perfile.TOK_WORD, '')]

        with pytest.raises(perfile.ParseException):
            template.insert(values, coord, toks)

        assert values == {'structure': []}
        assert not mock_InsertSection.called

    def test_bad_tok(self, mocker):
        mock_InsertSection = mocker.patch.object(template, 'InsertSection')
        values = {'structure': []}
        coord = location.Coordinate('path', 23)
        toks = [perfile.Token(perfile.TOK_CHAR, '{')]

        with pytest.raises(perfile.ParseException):
            template.insert(values, coord, toks)

        assert values == {'structure': []}
        assert not mock_InsertSection.called


class TestLiteralDirective(object):
    def test_init_base(self):
        values = {'structure': []}
        coord = location.Coordinate('path', 23)
        toks = [perfile.Token(perfile.TOK_CHAR, '{')]

        result = template.LiteralDirective(values, coord, toks)

        assert result.values is values
        assert result.start_coord == coord
        assert values == {'structure': []}

    def test_init_too_many_toks(self):
        values = {'structure': []}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'something'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            template.LiteralDirective(values, coord, toks)

        assert values == {'structure': []}

    def test_init_bad_tok(self):
        values = {'structure': []}
        coord = location.Coordinate('path', 23)
        toks = [perfile.Token(perfile.TOK_CHAR, '(')]

        with pytest.raises(perfile.ParseException):
            template.LiteralDirective(values, coord, toks)

        assert values == {'structure': []}

    def test_call_base(self, mocker):
        mock_Literal = mocker.patch.object(template, 'Literal')
        values = {'structure': []}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [perfile.Token(perfile.TOK_CHAR, '{')]
        end_toks = []
        obj = template.LiteralDirective(values, start_coord, start_toks)

        result = obj(end_coord, 'buf', end_toks)

        assert result is None
        assert values == {
            'structure': [mock_Literal.return_value],
        }
        mock_Literal.assert_called_once_with(
            location.CoordinateRange('path', 23, 42), 'buf'
        )

    def test_call_unclosed(self, mocker):
        mock_Literal = mocker.patch.object(template, 'Literal')
        values = {'structure': []}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [perfile.Token(perfile.TOK_CHAR, '{')]
        end_toks = None
        obj = template.LiteralDirective(values, start_coord, start_toks)

        with pytest.raises(perfile.ParseException):
            obj(end_coord, 'buf', end_toks)

        assert values == {'structure': []}
        assert not mock_Literal.called

    def test_call_bad_end(self, mocker):
        mock_Literal = mocker.patch.object(template, 'Literal')
        values = {'structure': []}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [perfile.Token(perfile.TOK_CHAR, '{')]
        end_toks = [perfile.Token(perfile.TOK_CHAR, '}')]
        obj = template.LiteralDirective(values, start_coord, start_toks)

        with pytest.raises(perfile.ParseException):
            obj(end_coord, 'buf', end_toks)

        assert values == {'structure': []}
        assert not mock_Literal.called


class TestDefineDirective(object):
    def test_initial(self):
        result = template.TemplateParser.DIRECTIVES['define'].init()

        assert isinstance(result, collections.OrderedDict)
        assert result == {}

    def test_init_base(self):
        values = {'defines': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'define'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        result = template.DefineDirective(values, coord, toks)

        assert result.name == 'define'
        assert result.values is values
        assert result.start_coord == coord
        assert values == {'defines': {}}

    def test_init_missing_toks(self):
        values = {'defines': {}}
        coord = location.Coordinate('path', 23)
        toks = [perfile.Token(perfile.TOK_CHAR, '{')]

        with pytest.raises(perfile.ParseException):
            template.DefineDirective(values, coord, toks)

        assert values == {'defines': {}}

    def test_init_bad_name(self):
        values = {'defines': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_STR, 'define'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            template.DefineDirective(values, coord, toks)

        assert values == {'defines': {}}

    def test_init_no_name(self):
        values = {'defines': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, ''),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            template.DefineDirective(values, coord, toks)

        assert values == {'defines': {}}

    def test_init_bad_brace(self):
        values = {'defines': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'define'),
            perfile.Token(perfile.TOK_CHAR, '('),
        ]

        with pytest.raises(perfile.ParseException):
            template.DefineDirective(values, coord, toks)

        assert values == {'defines': {}}

    def test_call_base(self, mocker):
        mock_Define = mocker.patch.object(template, 'Define')
        values = {'defines': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'define'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = []
        obj = template.DefineDirective(values, start_coord, start_toks)

        result = obj(end_coord, 'buf', end_toks)

        assert result is None
        assert values == {
            'defines': {'define': mock_Define.return_value},
        }
        mock_Define.assert_called_once_with(
            location.CoordinateRange('path', 23, 42), 'define', 'buf'
        )

    def test_call_unclosed(self, mocker):
        mock_Define = mocker.patch.object(template, 'Define')
        values = {'defines': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'define'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = None
        obj = template.DefineDirective(values, start_coord, start_toks)

        with pytest.raises(perfile.ParseException):
            obj(end_coord, 'buf', end_toks)

        assert values == {'defines': {}}
        assert not mock_Define.called

    def test_call_bad_end(self, mocker):
        mock_Define = mocker.patch.object(template, 'Define')
        values = {'defines': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'define'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = [perfile.Token(perfile.TOK_CHAR, '}')]
        obj = template.DefineDirective(values, start_coord, start_toks)

        with pytest.raises(perfile.ParseException):
            obj(end_coord, 'buf', end_toks)

        assert values == {'defines': {}}
        assert not mock_Define.called


class TestSectionDirective(object):
    def test_initial(self):
        result = template.TemplateParser.DIRECTIVES['section'].init()

        assert result == {}

    def test_init_base(self):
        values = {'sections': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'section'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        result = template.SectionDirective(values, coord, toks)

        assert result.name == 'section'
        assert result.requires == set()
        assert result.values is values
        assert result.start_coord == coord
        assert values == {'sections': {}}

    def test_init_one_require(self):
        values = {'sections': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'section'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'var1'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        result = template.SectionDirective(values, coord, toks)

        assert result.name == 'section'
        assert result.requires == {'var1'}
        assert result.values is values
        assert result.start_coord == coord
        assert values == {'sections': {}}

    def test_init_multi_requires(self):
        values = {'sections': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'section'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'var1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'var2'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'var3'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        result = template.SectionDirective(values, coord, toks)

        assert result.name == 'section'
        assert result.requires == {'var1', 'var2', 'var3'}
        assert result.values is values
        assert result.start_coord == coord
        assert values == {'sections': {}}

    def test_init_no_requires(self):
        values = {'sections': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'section'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            template.SectionDirective(values, coord, toks)

        assert values == {'sections': {}}

    def test_init_bad_requires(self):
        values = {'sections': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'section'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'var1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_STR, 'var2'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'var3'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            template.SectionDirective(values, coord, toks)

        assert values == {'sections': {}}

    def test_init_missing_open_paren(self):
        values = {'sections': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'section'),
            perfile.Token(perfile.TOK_WORD, 'var1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'var2'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'var3'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            template.SectionDirective(values, coord, toks)

        assert values == {'sections': {}}

    def test_init_missing_close_paren(self):
        values = {'sections': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'section'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'var1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'var2'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'var3'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            template.SectionDirective(values, coord, toks)

        assert values == {'sections': {}}

    def test_init_missing_toks(self):
        values = {'sections': {}}
        coord = location.Coordinate('path', 23)
        toks = [perfile.Token(perfile.TOK_CHAR, '{')]

        with pytest.raises(perfile.ParseException):
            template.SectionDirective(values, coord, toks)

        assert values == {'sections': {}}

    def test_init_bad_name(self):
        values = {'sections': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_STR, 'section'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            template.SectionDirective(values, coord, toks)

        assert values == {'sections': {}}

    def test_init_no_name(self):
        values = {'sections': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, ''),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            template.SectionDirective(values, coord, toks)

        assert values == {'sections': {}}

    def test_init_bad_brace(self):
        values = {'sections': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'section'),
            perfile.Token(perfile.TOK_CHAR, '('),
        ]

        with pytest.raises(perfile.ParseException):
            template.SectionDirective(values, coord, toks)

        assert values == {'sections': {}}

    def test_call_base(self, mocker):
        mock_Section = mocker.patch.object(template, 'Section')
        values = {'sections': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'section'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'var1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'var2'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'var3'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = []
        obj = template.SectionDirective(values, start_coord, start_toks)

        result = obj(end_coord, 'buf', end_toks)

        assert result is None
        assert values == {
            'sections': {'section': mock_Section.return_value},
        }
        mock_Section.assert_called_once_with(
            location.CoordinateRange('path', 23, 42),
            'section',
            {'var1', 'var2', 'var3'},
            'buf',
        )

    def test_call_unclosed(self, mocker):
        mock_Section = mocker.patch.object(template, 'Section')
        values = {'sections': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'section'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'var1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'var2'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'var3'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = None
        obj = template.SectionDirective(values, start_coord, start_toks)

        with pytest.raises(perfile.ParseException):
            obj(end_coord, 'buf', end_toks)

        assert values == {'sections': {}}
        assert not mock_Section.called

    def test_call_bad_end(self, mocker):
        mock_Section = mocker.patch.object(template, 'Section')
        values = {'sections': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'section'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'var1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'var2'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'var3'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = [perfile.Token(perfile.TOK_CHAR, '}')]
        obj = template.SectionDirective(values, start_coord, start_toks)

        with pytest.raises(perfile.ParseException):
            obj(end_coord, 'buf', end_toks)

        assert values == {'sections': {}}
        assert not mock_Section.called


class TestRenderContext(object):
    def test_init(self):
        result = template.RenderContext()

        assert isinstance(result.output, linelist.LineList)
        assert list(result.output) == []
        assert isinstance(result.sections, collections.defaultdict)
        assert list(result.sections['spam']) == []


def _fake_elem_render(ctxt):
    result = []
    for _name, sect in sorted(ctxt.sections.items(), key=lambda x: x[0]):
        result.extend(sect)

    return result


class TestTemplate(object):
    def test_get_tmpl_cached(self, mocker):
        mocker.patch.dict(template.Template._tmpl_cache, clear=True)
        mock_resource_stream = mocker.patch.object(
            template.pkg_resources, 'resource_stream'
        )
        mock_TextIOWrapper = mocker.patch.object(template.io, 'TextIOWrapper')
        mock_TemplateParser = mocker.patch.object(template, 'TemplateParser')
        mock_init = mocker.patch.object(
            template.Template, '__init__', return_value=None
        )
        template.Template._tmpl_cache['spam.c'] = 'cached'

        result = template.Template.get_tmpl('spam.c')

        assert result == 'cached'
        assert not mock_resource_stream.called
        assert not mock_TextIOWrapper.called
        assert not mock_TemplateParser.called
        assert not mock_TemplateParser.return_value.parse.called
        assert not mock_init.called
        assert template.Template._tmpl_cache == {'spam.c': 'cached'}

    def test_get_tmpl_uncached(self, mocker):
        mocker.patch.dict(template.Template._tmpl_cache, clear=True)
        mock_resource_stream = mocker.patch.object(
            template.pkg_resources, 'resource_stream'
        )
        mock_TextIOWrapper = mocker.patch.object(template.io, 'TextIOWrapper')
        tmpl = mocker.Mock(**{
            'parse.return_value': {'a': 1, 'b': 2, 'c': 3},
        })
        mock_TemplateParser = mocker.patch.object(
            template, 'TemplateParser', return_value=tmpl
        )
        mock_init = mocker.patch.object(
            template.Template, '__init__', return_value=None
        )

        result = template.Template.get_tmpl('spam.c')

        assert isinstance(result, template.Template)
        mock_resource_stream.assert_called_once_with(
            'hypocrite', template.TEMPLATES % 'spam.c'
        )
        mock_TextIOWrapper.assert_called_once_with(
            mock_resource_stream.return_value
        )
        mock_TemplateParser.assert_called_once_with()
        tmpl.parse.assert_called_once_with(
            mock_TextIOWrapper.return_value, 'spam.c'
        )
        mock_init.assert_called_once_with('spam.c', a=1, b=2, c=3)
        assert template.Template._tmpl_cache == {'spam.c': result}

    def test_init(self):
        result = template.Template('name', 'structure', 'defines', 'sections')

        assert result.name == 'name'
        assert result.structure == 'structure'
        assert result.defines == 'defines'
        assert result.sections == 'sections'

    def test_render(self, mocker):
        defines = collections.OrderedDict()
        defines['def1'] = mocker.Mock(**{
            'render.return_value': 'one line value',
        })
        defines['def2'] = mocker.Mock(**{
            'render.return_value': ['two line', 'value'],
        })
        sections = collections.OrderedDict()
        sections['sect1'] = mocker.Mock(**{
            'render.return_value': None,
        })
        sections['sect2'] = mocker.Mock(**{
            'render.return_value': ['sect2 line 1', 'sect2 line 2'],
        })
        sections['sect3'] = mocker.Mock(**{
            'render.side_effect': lambda kwargs: [
                '%s=%s' % (k, v)
                for k, v in sorted(kwargs.items(), key=lambda x: x[0])
            ],
        })
        structure = [
            mocker.Mock(**{
                'render.return_value': ['line 1', 'line 2', 'line 3'],
            }),
            mocker.Mock(**{
                'render.side_effect': _fake_elem_render,
            }),
            mocker.Mock(**{
                'render.return_value': ['line 4', 'line 5', 'line 6'],
            }),
        ]
        ctxt = template.RenderContext()
        obj = template.Template('spam.c', structure, defines, sections)

        result = obj.render(ctxt, a=1, b=2, c=3)

        assert result is ctxt.output
        assert list(result) == [
            'line 1',
            'line 2',
            'line 3',
            'sect2 line 1',
            'sect2 line 2',
            'a=1',
            'b=2',
            'c=3',
            'def1=one line value',
            "def2=['two line', 'value']",
            'line 4',
            'line 5',
            'line 6',
        ]
