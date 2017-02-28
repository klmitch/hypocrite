import collections

import pytest
from six.moves import builtins

from hypocrite import hypofile
from hypocrite import location
from hypocrite import perfile


class TestExtractType(object):
    def test_base(self):
        toks = [
            (perfile.TOK_WORD, 'void'),
            (perfile.TOK_CHAR, '*'),
            (perfile.TOK_WORD, 'function'),
            (perfile.TOK_CHAR, '('),
            (perfile.TOK_WORD, 'const'),
            (perfile.TOK_WORD, 'struct'),
            (perfile.TOK_WORD, 'name_s'),
            (perfile.TOK_CHAR, '*'),
            (perfile.TOK_CHAR, '*'),
            (perfile.TOK_WORD, 'arg1'),
            (perfile.TOK_CHAR, ','),
            (perfile.TOK_WORD, 'int'),
            (perfile.TOK_WORD, 'arg2'),
            (perfile.TOK_CHAR, ')'),
        ]
        delims = {
            (perfile.TOK_CHAR, '('),
            (perfile.TOK_CHAR, ','),
            (perfile.TOK_CHAR, ')'),
        }

        result = list(hypofile._extract_type(toks, delims))

        assert result == [
            (
                [
                    (perfile.TOK_WORD, 'void'),
                    (perfile.TOK_CHAR, '*'),
                ],
                (perfile.TOK_WORD, 'function'),
                (perfile.TOK_CHAR, '('),
            ),
            (
                [
                    (perfile.TOK_WORD, 'const'),
                    (perfile.TOK_WORD, 'struct'),
                    (perfile.TOK_WORD, 'name_s'),
                    (perfile.TOK_CHAR, '*'),
                    (perfile.TOK_CHAR, '*'),
                ],
                (perfile.TOK_WORD, 'arg1'),
                (perfile.TOK_CHAR, ','),
            ),
            (
                [
                    (perfile.TOK_WORD, 'int'),
                ],
                (perfile.TOK_WORD, 'arg2'),
                (perfile.TOK_CHAR, ')'),
            ),
            ([], None, None),
        ]


class TestMakeType(object):
    def test_one_tok(self):
        toks = [
            perfile.Token(perfile.TOK_WORD, 'void'),
        ]

        result = hypofile._make_type(toks, 'spam', 'coord')

        assert result == 'void'

    def test_multi_tok(self):
        toks = [
            perfile.Token(perfile.TOK_WORD, 'const'),
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'name_s'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_CHAR, '*'),
        ]

        result = hypofile._make_type(toks, 'spam', 'coord')

        assert result == 'const struct name_s **'

    def test_nonword(self):
        toks = [
            perfile.Token(perfile.TOK_WORD, 'const'),
            perfile.Token(perfile.TOK_STR, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'name_s'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_CHAR, '*'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile._make_type(toks, 'spam', 'coord')

    def test_badchar(self):
        toks = [
            perfile.Token(perfile.TOK_WORD, 'const'),
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'name_s'),
            perfile.Token(perfile.TOK_CHAR, '%'),
            perfile.Token(perfile.TOK_CHAR, '*'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile._make_type(toks, 'spam', 'coord')


class TestPreamble(object):
    def test_init(self):
        result = hypofile.Preamble('range', 'code')

        assert result.coord_range == 'range'
        assert result.code == 'code'

    def test_render(self, mocker):
        ctxt = mocker.Mock(sections={'preamble': ['l0']})
        obj = hypofile.Preamble('range', ['l1', 'l2', 'l3'])

        obj.render('hfile', ctxt)

        assert ctxt.sections == {'preamble': ['l0', 'l1', 'l2', 'l3']}


class TestHypocriteTest(object):
    def test_init(self):
        result = hypofile.HypocriteTest('range', 'name', 'code', 'fixtures')

        assert result.coord_range == 'range'
        assert result.name == 'name'
        assert result.code == 'code'
        assert result.fixtures == 'fixtures'

    def test_render(self, mocker):
        hfile = mocker.Mock(fixtures={
            'fix1': 'fixture1',
            'fix2': 'fixture2',
            'fix3': 'fixture3',
        })
        mock_get_tmpl = mocker.patch.object(
            hypofile.template.Template, 'get_tmpl'
        )
        obj = hypofile.HypocriteTest('range', 'name', 'code', [
            ('fix1', True),
            ('fix2', False),
            ('fix3', True),
        ])

        obj.render(hfile, 'ctxt')

        mock_get_tmpl.assert_called_once_with(hypofile.HypocriteTest.TEMPLATE)
        mock_get_tmpl.return_value.render.assert_called_once_with(
            'ctxt',
            name='name',
            code='code',
            fixtures=[
                ('fixture1', True),
                ('fixture2', False),
                ('fixture3', True),
            ],
        )


class TestHypocriteMock(object):
    def test_init(self):
        result = hypofile.HypocriteMock('range', 'name', 'return_type', 'args')

        assert result.coord_range == 'range'
        assert result.name == 'name'
        assert result.return_type == 'return_type'
        assert result.args == 'args'

    def test_render_void(self, mocker):
        mock_get_tmpl = mocker.patch.object(
            hypofile.template.Template, 'get_tmpl'
        )
        obj = hypofile.HypocriteMock('range', 'name', 'void', 'args')

        obj.render('hfile', 'ctxt')

        mock_get_tmpl.assert_called_once_with(
            hypofile.HypocriteMock.TEMPLATE_VOID
        )
        mock_get_tmpl.return_value.render.assert_called_once_with(
            'ctxt',
            name='name',
            return_type='void',
            args='args',
        )

    def test_render_nonvoid(self, mocker):
        mock_get_tmpl = mocker.patch.object(
            hypofile.template.Template, 'get_tmpl'
        )
        obj = hypofile.HypocriteMock('range', 'name', 'int', 'args')

        obj.render('hfile', 'ctxt')

        mock_get_tmpl.assert_called_once_with(hypofile.HypocriteMock.TEMPLATE)
        mock_get_tmpl.return_value.render.assert_called_once_with(
            'ctxt',
            name='name',
            return_type='int',
            args='args',
        )


class TestFixture(object):
    def test_init_base(self):
        result = hypofile.Fixture('range', 'name', 'return_type', 'code')

        assert result.coord_range == 'range'
        assert result.name == 'name'
        assert result.return_type == 'return_type'
        assert result.code == 'code'
        assert result.teardown is None

    def test_init_teardown(self):
        result = hypofile.Fixture(
            'range', 'name', 'return_type', 'code', 'teardown'
        )

        assert result.coord_range == 'range'
        assert result.name == 'name'
        assert result.return_type == 'return_type'
        assert result.code == 'code'
        assert result.teardown == 'teardown'

    def test_render_base(self, mocker):
        mock_get_tmpl = mocker.patch.object(
            hypofile.template.Template, 'get_tmpl'
        )
        obj = hypofile.Fixture('range', 'name', 'return_type', 'code')

        obj.render('hfile', 'ctxt')

        mock_get_tmpl.assert_called_once_with(hypofile.Fixture.TEMPLATE)
        mock_get_tmpl.return_value.render.assert_called_once_with(
            'ctxt',
            name='name',
            return_type='return_type',
            code='code',
        )

    def test_render_teardown(self, mocker):
        mock_get_tmpl = mocker.patch.object(
            hypofile.template.Template, 'get_tmpl'
        )
        obj = hypofile.Fixture(
            'range', 'name', 'return_type', 'code', 'teardown'
        )

        obj.render('hfile', 'ctxt')

        mock_get_tmpl.assert_called_once_with(hypofile.Fixture.TEMPLATE)
        mock_get_tmpl.return_value.render.assert_called_once_with(
            'ctxt',
            name='name',
            return_type='return_type',
            code='code',
            teardown='teardown',
        )


class TestTargetDirective(object):
    def test_base(self):
        values = {'target': None}
        coord = location.Coordinate('path', 23)
        toks = [perfile.Token(perfile.TOK_STR, 'target.c')]

        result = hypofile.target_directive(values, coord, toks)

        assert result is None
        assert values == {'target': 'target.c'}

    def test_too_many_toks(self):
        values = {'target': None}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_STR, 'target.c'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.target_directive(values, coord, toks)

        assert values == {'target': None}

    def test_empty_tok(self):
        values = {'target': None}
        coord = location.Coordinate('path', 23)
        toks = [perfile.Token(perfile.TOK_STR, '')]

        with pytest.raises(perfile.ParseException):
            hypofile.target_directive(values, coord, toks)

        assert values == {'target': None}

    def test_bad_tok(self):
        values = {'target': None}
        coord = location.Coordinate('path', 23)
        toks = [perfile.Token(perfile.TOK_WORD, 'target.c')]

        with pytest.raises(perfile.ParseException):
            hypofile.target_directive(values, coord, toks)

        assert values == {'target': None}


class TestPreambleDirective(object):
    def test_initial(self):
        result = hypofile.HypoParser.DIRECTIVES['preamble'].init()

        assert result == []

    def test_init_base(self):
        values = {'preamble': []}
        coord = location.Coordinate('path', 23)
        toks = [perfile.Token(perfile.TOK_CHAR, '{')]

        result = hypofile.PreambleDirective(values, coord, toks)

        assert result.values is values
        assert result.start_coord == coord
        assert values == {'preamble': []}

    def test_init_too_many_toks(self):
        values = {'preamble': []}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'first'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.PreambleDirective(values, coord, toks)

        assert values == {'preamble': []}

    def test_init_bad_tok(self):
        values = {'preamble': []}
        coord = location.Coordinate('path', 23)
        toks = [perfile.Token(perfile.TOK_CHAR, '(')]

        with pytest.raises(perfile.ParseException):
            hypofile.PreambleDirective(values, coord, toks)

        assert values == {'preamble': []}

    def test_call_base(self, mocker):
        mock_Preamble = mocker.patch.object(hypofile, 'Preamble')
        values = {'preamble': []}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [perfile.Token(perfile.TOK_CHAR, '{')]
        end_toks = []
        obj = hypofile.PreambleDirective(values, start_coord, start_toks)

        result = obj(end_coord, 'buf', end_toks)

        assert result is None
        assert values == {
            'preamble': [mock_Preamble.return_value],
        }
        mock_Preamble.assert_called_once_with(
            location.CoordinateRange('path', 23, 42), 'buf'
        )

    def test_call_unclosed(self, mocker):
        mock_Preamble = mocker.patch.object(hypofile, 'Preamble')
        values = {'preamble': []}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [perfile.Token(perfile.TOK_CHAR, '{')]
        end_toks = None
        obj = hypofile.PreambleDirective(values, start_coord, start_toks)

        with pytest.raises(perfile.ParseException):
            obj(end_coord, 'buf', end_toks)

        assert values == {'preamble': []}
        assert not mock_Preamble.called

    def test_call_bad_end(self, mocker):
        mock_Preamble = mocker.patch.object(hypofile, 'Preamble')
        values = {'preamble': []}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [perfile.Token(perfile.TOK_CHAR, '{')]
        end_toks = [perfile.Token(perfile.TOK_CHAR, '}')]
        obj = hypofile.PreambleDirective(values, start_coord, start_toks)

        with pytest.raises(perfile.ParseException):
            obj(end_coord, 'buf', end_toks)

        assert values == {'preamble': []}
        assert not mock_Preamble.called


class TestMockDirective(object):
    def test_initial(self):
        result = hypofile.HypoParser.DIRECTIVES['mock'].init()

        assert result == {}

    def test_base(self, mocker):
        mock_HypocriteMock = mocker.patch.object(hypofile, 'HypocriteMock')
        values = {'mocks': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'st_name'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'func_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_CHAR, ')'),
        ]

        result = hypofile.mock(values, coord, toks)

        assert result is None
        assert values == {
            'mocks': {
                'func_name': mock_HypocriteMock.return_value,
            },
        }
        mock_HypocriteMock.assert_called_once_with(
            location.CoordinateRange('path', 23, 23),
            'func_name',
            'struct st_name *',
            [],
        )

    def test_void(self, mocker):
        mock_HypocriteMock = mocker.patch.object(hypofile, 'HypocriteMock')
        values = {'mocks': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'st_name'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'func_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'void'),
            perfile.Token(perfile.TOK_CHAR, ')'),
        ]

        result = hypofile.mock(values, coord, toks)

        assert result is None
        assert values == {
            'mocks': {
                'func_name': mock_HypocriteMock.return_value,
            },
        }
        mock_HypocriteMock.assert_called_once_with(
            location.CoordinateRange('path', 23, 23),
            'func_name',
            'struct st_name *',
            [],
        )

    def test_with_args(self, mocker):
        mock_HypocriteMock = mocker.patch.object(hypofile, 'HypocriteMock')
        values = {'mocks': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'st_name'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'func_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'void'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'arg1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'arg2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
        ]

        result = hypofile.mock(values, coord, toks)

        assert result is None
        assert values == {
            'mocks': {
                'func_name': mock_HypocriteMock.return_value,
            },
        }
        mock_HypocriteMock.assert_called_once_with(
            location.CoordinateRange('path', 23, 23),
            'func_name',
            'struct st_name *',
            [('void *', 'arg1'), ('int', 'arg2')],
        )

    def test_missing_prefix(self, mocker):
        mock_HypocriteMock = mocker.patch.object(hypofile, 'HypocriteMock')
        values = {'mocks': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'void'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'arg1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'arg2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.mock(values, coord, toks)

        assert values == {'mocks': {}}
        assert not mock_HypocriteMock.called

    def test_bad_func_name(self, mocker):
        mock_HypocriteMock = mocker.patch.object(hypofile, 'HypocriteMock')
        values = {'mocks': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'st_name'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_STR, 'func_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'void'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'arg1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'arg2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.mock(values, coord, toks)

        assert values == {'mocks': {}}
        assert not mock_HypocriteMock.called

    def test_empty_name(self, mocker):
        mock_HypocriteMock = mocker.patch.object(hypofile, 'HypocriteMock')
        values = {'mocks': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'st_name'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, ''),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'void'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'arg1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'arg2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.mock(values, coord, toks)

        assert values == {'mocks': {}}
        assert not mock_HypocriteMock.called

    def test_wrong_initial_delim(self, mocker):
        mock_HypocriteMock = mocker.patch.object(hypofile, 'HypocriteMock')
        values = {'mocks': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'st_name'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'func_name'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_WORD, 'void'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'arg1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'arg2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.mock(values, coord, toks)

        assert values == {'mocks': {}}
        assert not mock_HypocriteMock.called

    def test_trailing_tokens(self, mocker):
        mock_HypocriteMock = mocker.patch.object(hypofile, 'HypocriteMock')
        values = {'mocks': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'st_name'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'func_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'void'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'arg1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'arg2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_WORD, 'unexpected'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.mock(values, coord, toks)

        assert values == {'mocks': {}}
        assert not mock_HypocriteMock.called

    def test_premature_end(self, mocker):
        mock_HypocriteMock = mocker.patch.object(hypofile, 'HypocriteMock')
        values = {'mocks': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'st_name'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'func_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'void'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'arg1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'arg2'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.mock(values, coord, toks)

        assert values == {'mocks': {}}
        assert not mock_HypocriteMock.called

    def test_empty_arg(self, mocker):
        mock_HypocriteMock = mocker.patch.object(hypofile, 'HypocriteMock')
        values = {'mocks': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'st_name'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'func_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'void'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'arg1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'arg2'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_CHAR, ')'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.mock(values, coord, toks)

        assert values == {'mocks': {}}
        assert not mock_HypocriteMock.called

    def test_bad_name(self, mocker):
        mock_HypocriteMock = mocker.patch.object(hypofile, 'HypocriteMock')
        values = {'mocks': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'st_name'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'func_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'void'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'arg1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_STR, 'arg2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.mock(values, coord, toks)

        assert values == {'mocks': {}}
        assert not mock_HypocriteMock.called

    def test_no_name(self, mocker):
        mock_HypocriteMock = mocker.patch.object(hypofile, 'HypocriteMock')
        values = {'mocks': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'st_name'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'func_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'void'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'arg1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, ''),
            perfile.Token(perfile.TOK_CHAR, ')'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.mock(values, coord, toks)

        assert values == {'mocks': {}}
        assert not mock_HypocriteMock.called

    def test_bad_delim(self, mocker):
        mock_HypocriteMock = mocker.patch.object(hypofile, 'HypocriteMock')
        values = {'mocks': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'st_name'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'func_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'void'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'arg1'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'arg2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.mock(values, coord, toks)

        assert values == {'mocks': {}}
        assert not mock_HypocriteMock.called

    def test_no_args(self, mocker):
        mock_HypocriteMock = mocker.patch.object(hypofile, 'HypocriteMock')
        values = {'mocks': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'st_name'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'func_name'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.mock(values, coord, toks)

        assert values == {'mocks': {}}
        assert not mock_HypocriteMock.called


class TestTestDirective(object):
    def test_initial(self):
        result = hypofile.HypoParser.DIRECTIVES['test'].init()

        assert isinstance(result, collections.OrderedDict)
        assert result == {}

    def test_init_base(self):
        values = {'tests': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'test_name'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        result = hypofile.TestDirective(values, coord, toks)

        assert result.name == 'test_name'
        assert result.fixtures == []
        assert result.values is values
        assert result.start_coord == coord
        assert values == {'tests': {}}

    def test_init_with_fixtures(self):
        values = {'tests': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'test_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'fix1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_CHAR, '!'),
            perfile.Token(perfile.TOK_WORD, 'fix2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        result = hypofile.TestDirective(values, coord, toks)

        assert result.name == 'test_name'
        assert result.fixtures == [
            ('fix1', True),
            ('fix2', False),
        ]
        assert result.values is values
        assert result.start_coord == coord
        assert values == {'tests': {}}

    def test_init_no_fixtures(self):
        values = {'tests': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'test_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.TestDirective(values, coord, toks)

        assert values == {'tests': {}}

    def test_init_too_few_tokens(self):
        values = {'tests': {}}
        coord = location.Coordinate('path', 23)
        toks = [perfile.Token(perfile.TOK_WORD, 'test_name')]

        with pytest.raises(perfile.ParseException):
            hypofile.TestDirective(values, coord, toks)

        assert values == {'tests': {}}

    def test_init_bad_name(self):
        values = {'tests': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_STR, 'test_name'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.TestDirective(values, coord, toks)

        assert values == {'tests': {}}

    def test_init_empty_name(self):
        values = {'tests': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, ''),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.TestDirective(values, coord, toks)

        assert values == {'tests': {}}

    def test_init_bad_brace(self):
        values = {'tests': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'test_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.TestDirective(values, coord, toks)

        assert values == {'tests': {}}

    def test_init_bad_fixture_open_paren(self):
        values = {'tests': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'test_name'),
            perfile.Token(perfile.TOK_CHAR, '['),
            perfile.Token(perfile.TOK_WORD, 'fix1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_CHAR, '!'),
            perfile.Token(perfile.TOK_WORD, 'fix2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.TestDirective(values, coord, toks)

        assert values == {'tests': {}}

    def test_init_bad_fixture_close_paren(self):
        values = {'tests': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'test_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'fix1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_CHAR, '!'),
            perfile.Token(perfile.TOK_WORD, 'fix2'),
            perfile.Token(perfile.TOK_CHAR, ']'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.TestDirective(values, coord, toks)

        assert values == {'tests': {}}

    def test_init_too_few_fixture_tokens(self):
        values = {'tests': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'test_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_CHAR, '!'),
            perfile.Token(perfile.TOK_WORD, 'fix2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.TestDirective(values, coord, toks)

        assert values == {'tests': {}}

    def test_init_too_many_fixture_tokens(self):
        values = {'tests': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'test_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'fix1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_CHAR, '!'),
            perfile.Token(perfile.TOK_CHAR, '!'),
            perfile.Token(perfile.TOK_WORD, 'fix2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.TestDirective(values, coord, toks)

        assert values == {'tests': {}}

    def test_init_bad_fixture_name(self):
        values = {'tests': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'test_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_STR, 'fix1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_CHAR, '!'),
            perfile.Token(perfile.TOK_WORD, 'fix2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.TestDirective(values, coord, toks)

        assert values == {'tests': {}}

    def test_init_empty_fixture_name(self):
        values = {'tests': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'test_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, ''),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_CHAR, '!'),
            perfile.Token(perfile.TOK_WORD, 'fix2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.TestDirective(values, coord, toks)

        assert values == {'tests': {}}

    def test_init_bad_fixture_prefix(self):
        values = {'tests': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'test_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'fix1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_CHAR, '^'),
            perfile.Token(perfile.TOK_WORD, 'fix2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.TestDirective(values, coord, toks)

        assert values == {'tests': {}}

    def test_call_base(self, mocker):
        mock_HypocriteTest = mocker.patch.object(hypofile, 'HypocriteTest')
        values = {'tests': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'test_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'fix1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_CHAR, '!'),
            perfile.Token(perfile.TOK_WORD, 'fix2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = []
        obj = hypofile.TestDirective(values, start_coord, start_toks)

        result = obj(end_coord, 'buf', end_toks)

        assert result is None
        assert values == {
            'tests': {
                'test_name': mock_HypocriteTest.return_value,
            },
        }
        mock_HypocriteTest.assert_called_once_with(
            location.CoordinateRange('path', 23, 42),
            'test_name',
            'buf',
            [('fix1', True), ('fix2', False)],
        )

    def test_call_unclosed(self, mocker):
        mock_HypocriteTest = mocker.patch.object(hypofile, 'HypocriteTest')
        values = {'tests': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'test_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'fix1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_CHAR, '!'),
            perfile.Token(perfile.TOK_WORD, 'fix2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = None
        obj = hypofile.TestDirective(values, start_coord, start_toks)

        with pytest.raises(perfile.ParseException):
            obj(end_coord, 'buf', end_toks)

        assert values == {'tests': {}}
        assert not mock_HypocriteTest.called

    def test_call_bad_end(self, mocker):
        mock_HypocriteTest = mocker.patch.object(hypofile, 'HypocriteTest')
        values = {'tests': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'test_name'),
            perfile.Token(perfile.TOK_CHAR, '('),
            perfile.Token(perfile.TOK_WORD, 'fix1'),
            perfile.Token(perfile.TOK_CHAR, ','),
            perfile.Token(perfile.TOK_CHAR, '!'),
            perfile.Token(perfile.TOK_WORD, 'fix2'),
            perfile.Token(perfile.TOK_CHAR, ')'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = [perfile.Token(perfile.TOK_CHAR, '}')]
        obj = hypofile.TestDirective(values, start_coord, start_toks)

        with pytest.raises(perfile.ParseException):
            obj(end_coord, 'buf', end_toks)

        assert values == {'tests': {}}
        assert not mock_HypocriteTest.called


class TestFixtureDirective(object):
    def test_initial(self):
        result = hypofile.HypoParser.DIRECTIVES['fixture'].init()

        assert result == {}

    def test_init_base(self):
        values = {'fixtures': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'fix_name'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        result = hypofile.FixtureDirective(values, coord, toks)

        assert result.name == 'fix_name'
        assert result.type_ is None
        assert result.values is values
        assert result.start_coord == coord
        assert result.block_start == coord
        assert values == {'fixtures': {}}

    def test_init_void(self):
        values = {'fixtures': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'void'),
            perfile.Token(perfile.TOK_WORD, 'fix_name'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        result = hypofile.FixtureDirective(values, coord, toks)

        assert result.name == 'fix_name'
        assert result.type_ is None
        assert result.values is values
        assert result.start_coord == coord
        assert result.block_start == coord
        assert values == {'fixtures': {}}

    def test_init_with_type(self):
        values = {'fixtures': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'struct'),
            perfile.Token(perfile.TOK_WORD, 'fix_s'),
            perfile.Token(perfile.TOK_CHAR, '*'),
            perfile.Token(perfile.TOK_WORD, 'fix_name'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        result = hypofile.FixtureDirective(values, coord, toks)

        assert result.name == 'fix_name'
        assert result.type_ == 'struct fix_s *'
        assert result.values is values
        assert result.start_coord == coord
        assert result.block_start == coord
        assert values == {'fixtures': {}}

    def test_init_trailing_tokens(self):
        values = {'fixtures': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, 'fix_name'),
            perfile.Token(perfile.TOK_CHAR, '{'),
            perfile.Token(perfile.TOK_WORD, 'unexpected'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.FixtureDirective(values, coord, toks)

        assert values == {'fixtures': {}}

    def test_init_missing_brace(self):
        values = {'fixtures': {}}
        coord = location.Coordinate('path', 23)
        toks = [perfile.Token(perfile.TOK_WORD, 'fix_name')]

        with pytest.raises(perfile.ParseException):
            hypofile.FixtureDirective(values, coord, toks)

        assert values == {'fixtures': {}}

    def test_init_missing_name(self):
        values = {'fixtures': {}}
        coord = location.Coordinate('path', 23)
        toks = [perfile.Token(perfile.TOK_CHAR, '{')]

        with pytest.raises(perfile.ParseException):
            hypofile.FixtureDirective(values, coord, toks)

        assert values == {'fixtures': {}}

    def test_init_bad_name(self):
        values = {'fixtures': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_STR, 'fix_name'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.FixtureDirective(values, coord, toks)

        assert values == {'fixtures': {}}

    def test_init_empty_name(self):
        values = {'fixtures': {}}
        coord = location.Coordinate('path', 23)
        toks = [
            perfile.Token(perfile.TOK_WORD, ''),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]

        with pytest.raises(perfile.ParseException):
            hypofile.FixtureDirective(values, coord, toks)

        assert values == {'fixtures': {}}

    def test_call_base(self, mocker):
        mock_Fixture = mocker.patch.object(hypofile, 'Fixture')
        values = {'fixtures': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'fix_name'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = []
        obj = hypofile.FixtureDirective(values, start_coord, start_toks)

        result = obj(end_coord, 'buf', end_toks)

        assert result is None
        assert values == {'fixtures': {'fix_name': mock_Fixture.return_value}}
        mock_Fixture.assert_called_once_with(
            location.CoordinateRange('path', 23, 42),
            'fix_name',
            'int',
            'buf',
        )

    def test_call_with_teardown(self, mocker):
        mock_Fixture = mocker.patch.object(hypofile, 'Fixture')
        values = {'fixtures': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'fix_name'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = [
            perfile.Token(perfile.TOK_WORD, 'teardown'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        obj = hypofile.FixtureDirective(values, start_coord, start_toks)

        result = obj(end_coord, 'buf', end_toks)

        assert result == obj.teardown
        assert obj.code == 'buf'
        assert obj.start_coord == start_coord
        assert obj.block_start == end_coord
        assert values == {'fixtures': {}}
        assert not mock_Fixture.called

    def test_call_unclosed(self, mocker):
        mock_Fixture = mocker.patch.object(hypofile, 'Fixture')
        values = {'fixtures': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'fix_name'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = None
        obj = hypofile.FixtureDirective(values, start_coord, start_toks)

        with pytest.raises(perfile.ParseException):
            obj(end_coord, 'buf', end_toks)

        assert values == {'fixtures': {}}
        assert not mock_Fixture.called

    def test_call_bad_teardown(self, mocker):
        mock_Fixture = mocker.patch.object(hypofile, 'Fixture')
        values = {'fixtures': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'fix_name'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = [
            perfile.Token(perfile.TOK_STR, 'teardown'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        obj = hypofile.FixtureDirective(values, start_coord, start_toks)

        with pytest.raises(perfile.ParseException):
            obj(end_coord, 'buf', end_toks)

        assert values == {'fixtures': {}}
        assert not mock_Fixture.called

    def test_teardown_base(self, mocker):
        mock_Fixture = mocker.patch.object(hypofile, 'Fixture')
        values = {'fixtures': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'fix_name'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = []
        obj = hypofile.FixtureDirective(values, start_coord, start_toks)
        obj.code = 'code'
        obj.block_start = location.Coordinate('path', 31)

        result = obj.teardown(end_coord, 'buf', end_toks)

        assert result is None
        assert values == {'fixtures': {'fix_name': mock_Fixture.return_value}}
        mock_Fixture.assert_called_once_with(
            location.CoordinateRange('path', 23, 42),
            'fix_name',
            'int',
            'code',
            'buf',
        )

    def test_teardown_unclosed(self, mocker):
        mock_Fixture = mocker.patch.object(hypofile, 'Fixture')
        values = {'fixtures': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'fix_name'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = None
        obj = hypofile.FixtureDirective(values, start_coord, start_toks)
        obj.code = 'code'
        obj.block_start = location.Coordinate('path', 31)

        with pytest.raises(perfile.ParseException):
            obj.teardown(end_coord, 'buf', end_toks)

        assert values == {'fixtures': {}}
        assert not mock_Fixture.called

    def test_teardown_bad_end(self, mocker):
        mock_Fixture = mocker.patch.object(hypofile, 'Fixture')
        values = {'fixtures': {}}
        start_coord = location.Coordinate('path', 23)
        end_coord = location.Coordinate('path', 42)
        start_toks = [
            perfile.Token(perfile.TOK_WORD, 'int'),
            perfile.Token(perfile.TOK_WORD, 'fix_name'),
            perfile.Token(perfile.TOK_CHAR, '{'),
        ]
        end_toks = [perfile.Token(perfile.TOK_CHAR, '}')]
        obj = hypofile.FixtureDirective(values, start_coord, start_toks)
        obj.code = 'code'
        obj.block_start = location.Coordinate('path', 31)

        with pytest.raises(perfile.ParseException):
            obj.teardown(end_coord, 'buf', end_toks)

        assert values == {'fixtures': {}}
        assert not mock_Fixture.called


def _make_fake_render(text):
    def _fake_render(hfile, ctxt):
        ctxt.rendered.append(text)

    return _fake_render


class TestHypoFile(object):
    def test_parse(self, mocker):
        parser = mocker.Mock(**{
            'parse.return_value': {'a': 1, 'b': 2, 'c': 3},
        })
        mock_HypoParser = mocker.patch.object(
            hypofile, 'HypoParser', return_value=parser
        )
        handle = mocker.MagicMock()
        handle.__enter__.return_value = handle
        mock_open = mocker.patch.object(builtins, 'open', return_value=handle)
        mock_init = mocker.patch.object(
            hypofile.HypoFile, '__init__', return_value=None
        )

        result = hypofile.HypoFile.parse('some/path')

        assert isinstance(result, hypofile.HypoFile)
        mock_HypoParser.assert_called_once_with()
        mock_open.assert_called_once_with('some/path', 'rU')
        parser.parse.assert_called_once_with(handle, 'some/path')
        mock_init.assert_called_once_with('some/path', a=1, b=2, c=3)

    def test_init(self):
        result = hypofile.HypoFile(
            'path', 'target', 'preamble', 'tests', 'mocks', 'fixtures'
        )

        assert result.path == 'path'
        assert result.target == 'target'
        assert result.preamble == 'preamble'
        assert result.tests == 'tests'
        assert result.mocks == 'mocks'
        assert result.fixtures == 'fixtures'

    def test_render(self, mocker):
        preamble = [
            mocker.Mock(**{'render.side_effect': _make_fake_render('pre1')}),
            mocker.Mock(**{'render.side_effect': _make_fake_render('pre2')}),
        ]
        tests = collections.OrderedDict()
        tests['test2'] = mocker.Mock(**{
            'render.side_effect': _make_fake_render('test2'),
        })
        tests['test1'] = mocker.Mock(**{
            'render.side_effect': _make_fake_render('test1'),
        })
        mocks = {
            'mock1': mocker.Mock(**{
                'render.side_effect': _make_fake_render('mock1'),
            }),
            'mock2': mocker.Mock(**{
                'render.side_effect': _make_fake_render('mock2'),
            }),
        }
        fixtures = {
            'fix1': mocker.Mock(**{
                'render.side_effect': _make_fake_render('fix1'),
            }),
            'fix2': mocker.Mock(**{
                'render.side_effect': _make_fake_render('fix2'),
            }),
        }
        ctxt = mocker.Mock(rendered=[])
        mock_RenderContext = mocker.patch.object(
            hypofile.template, 'RenderContext', return_value=ctxt
        )
        mock_get_tmpl = mocker.patch.object(
            hypofile.template.Template, 'get_tmpl'
        )
        tmpl = mock_get_tmpl.return_value
        obj = hypofile.HypoFile(
            'some/path', 'target', preamble, tests, mocks, fixtures
        )

        result = obj.render('test_fname')

        assert result == tmpl.render.return_value
        mock_RenderContext.assert_called_once_with()
        for pre in preamble:
            pre.render.assert_called_once_with(obj, ctxt)
        for test in tests.values():
            test.render.assert_called_once_with(obj, ctxt)
        for mock in mocks.values():
            mock.render.assert_called_once_with(obj, ctxt)
        for fix in fixtures.values():
            fix.render.assert_called_once_with(obj, ctxt)
        assert ctxt.rendered == [
            'pre1', 'pre2',
            'test2', 'test1',
            'mock1', 'mock2',
            'fix1', 'fix2',
        ]
        mock_get_tmpl.assert_called_once_with(hypofile.HypoFile.TEMPLATE)
        tmpl.render.assert_called_once_with(
            ctxt, source='path', target='target', test_fname='test_fname'
        )
