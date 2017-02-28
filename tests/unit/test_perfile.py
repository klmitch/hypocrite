import pytest
import six

from hypocrite import perfile


class TestSplitToks(object):
    def test_empty(self):
        toks = []
        delims = {(perfile.TOK_CHAR, ',')}

        result = list(perfile.split_toks(toks, delims))

        assert result == [[]]

    def test_empty_include(self):
        toks = []
        delims = {(perfile.TOK_CHAR, ',')}

        result = list(perfile.split_toks(toks, delims, True))

        assert result == [([], None)]

    def test_one(self):
        toks = [
            (perfile.TOK_CHAR, '!'),
            (perfile.TOK_WORD, 'something'),
        ]
        delims = {(perfile.TOK_CHAR, ',')}

        result = list(perfile.split_toks(toks, delims))

        assert result == [
            [
                (perfile.TOK_CHAR, '!'),
                (perfile.TOK_WORD, 'something'),
            ],
        ]

    def test_one_include(self):
        toks = [
            (perfile.TOK_CHAR, '!'),
            (perfile.TOK_WORD, 'something'),
        ]
        delims = {(perfile.TOK_CHAR, ',')}

        result = list(perfile.split_toks(toks, delims, True))

        assert result == [
            (
                [
                    (perfile.TOK_CHAR, '!'),
                    (perfile.TOK_WORD, 'something'),
                ], None
            ),
        ]

    def test_one_comma(self):
        toks = [
            (perfile.TOK_CHAR, '!'),
            (perfile.TOK_WORD, 'something'),
            (perfile.TOK_CHAR, ','),
        ]
        delims = {(perfile.TOK_CHAR, ',')}

        result = list(perfile.split_toks(toks, delims))

        assert result == [
            [
                (perfile.TOK_CHAR, '!'),
                (perfile.TOK_WORD, 'something'),
            ],
            [],
        ]

    def test_one_comma_include(self):
        toks = [
            (perfile.TOK_CHAR, '!'),
            (perfile.TOK_WORD, 'something'),
            (perfile.TOK_CHAR, ','),
        ]
        delims = {(perfile.TOK_CHAR, ',')}

        result = list(perfile.split_toks(toks, delims, True))

        assert result == [
            (
                [
                    (perfile.TOK_CHAR, '!'),
                    (perfile.TOK_WORD, 'something'),
                ], (perfile.TOK_CHAR, ',')
            ),
            ([], None),
        ]

    def test_multi(self):
        toks = [
            (perfile.TOK_CHAR, '!'),
            (perfile.TOK_WORD, 'something'),
            (perfile.TOK_CHAR, '('),
            (perfile.TOK_WORD, 'arg1'),
            (perfile.TOK_CHAR, ','),
            (perfile.TOK_WORD, 'arg2'),
            (perfile.TOK_CHAR, ')'),
        ]
        delims = {
            (perfile.TOK_CHAR, '('),
            (perfile.TOK_CHAR, ','),
            (perfile.TOK_CHAR, ')'),
        }

        result = list(perfile.split_toks(toks, delims))

        assert result == [
            [
                (perfile.TOK_CHAR, '!'),
                (perfile.TOK_WORD, 'something'),
            ],
            [
                (perfile.TOK_WORD, 'arg1'),
            ],
            [
                (perfile.TOK_WORD, 'arg2'),
            ],
            [],
        ]

    def test_multi_include(self):
        toks = [
            (perfile.TOK_CHAR, '!'),
            (perfile.TOK_WORD, 'something'),
            (perfile.TOK_CHAR, '('),
            (perfile.TOK_WORD, 'arg1'),
            (perfile.TOK_CHAR, ','),
            (perfile.TOK_WORD, 'arg2'),
            (perfile.TOK_CHAR, ')'),
        ]
        delims = {
            (perfile.TOK_CHAR, '('),
            (perfile.TOK_CHAR, ','),
            (perfile.TOK_CHAR, ')'),
        }

        result = list(perfile.split_toks(toks, delims, True))

        assert result == [
            (
                [
                    (perfile.TOK_CHAR, '!'),
                    (perfile.TOK_WORD, 'something'),
                ], (perfile.TOK_CHAR, '(')
            ),
            (
                [
                    (perfile.TOK_WORD, 'arg1'),
                ], (perfile.TOK_CHAR, ',')
            ),
            (
                [
                    (perfile.TOK_WORD, 'arg2'),
                ], (perfile.TOK_CHAR, ')')
            ),
            ([], None),
        ]


class TestDirective(object):
    def test_init(self):
        result = perfile.Directive('directive', 'value', 'init', 'impl')

        assert result.directive == 'directive'
        assert result.value == 'value'
        assert result.init == 'init'
        assert result.impl == 'impl'

    def test_call(self, mocker):
        impl = mocker.Mock()
        obj = perfile.Directive('directive', 'value', 'init', impl)

        result = obj('values', 'start_coord', 'toks')

        assert result == impl.return_value
        impl.assert_called_once_with('values', 'start_coord', 'toks')

    def test_initial_static(self):
        obj = perfile.Directive('directive', 'value', 'spam', 'impl')

        result = obj.initial()

        assert result == 'spam'

    def test_initial_callable(self, mocker):
        init = mocker.Mock()
        obj = perfile.Directive('directive', 'value', init, 'impl')

        result = obj.initial()

        assert result == init.return_value
        init.assert_called_once_with()


class ParserForTest(perfile.PerFileParser):
    DIRECTIVES = {}


def _fake_parse_line(coord, line, values):
    if line.strip() == 'continue':
        raise perfile.Continue()


class TestPerFileParser(object):
    def test_tokenize_base(self):
        text = 'this is a test !  Let "us" see"what"happens.'

        result = list(perfile.PerFileParser._tokenize(text, 'coord'))

        assert result == [
            (perfile.TOK_WORD, 'this'),
            (perfile.TOK_WORD, 'is'),
            (perfile.TOK_WORD, 'a'),
            (perfile.TOK_WORD, 'test'),
            (perfile.TOK_CHAR, '!'),
            (perfile.TOK_WORD, 'Let'),
            (perfile.TOK_STR, 'us'),
            (perfile.TOK_WORD, 'see'),
            (perfile.TOK_STR, 'what'),
            (perfile.TOK_WORD, 'happens'),
            (perfile.TOK_CHAR, '.'),
        ]

    def test_tokenize_end_word(self):
        text = 'ends with a word'

        result = list(perfile.PerFileParser._tokenize(text, 'coord'))

        assert result == [
            (perfile.TOK_WORD, 'ends'),
            (perfile.TOK_WORD, 'with'),
            (perfile.TOK_WORD, 'a'),
            (perfile.TOK_WORD, 'word'),
        ]

    def test_tokenize_unclosed_str(self):
        text = '"an unclosed string'

        with pytest.raises(perfile.ParseException):
            list(perfile.PerFileParser._tokenize(text, 'coord'))

    def test_directive_base(self, mocker):
        mocker.patch.dict(ParserForTest.DIRECTIVES)
        mock_Directive = mocker.patch.object(perfile, 'Directive')
        func = mocker.Mock(__name__='test_func')

        decorator = ParserForTest.directive()

        assert callable(decorator)
        assert ParserForTest.DIRECTIVES == {}
        assert not mock_Directive.called

        result = decorator(func)

        assert result == func
        assert ParserForTest.DIRECTIVES == {
            'test_func': mock_Directive.return_value,
        }
        mock_Directive.assert_called_once_with(
            'test_func', 'test_func', perfile._unset, func
        )
        assert not func.called

    def test_directive_name(self, mocker):
        mocker.patch.dict(ParserForTest.DIRECTIVES)
        mock_Directive = mocker.patch.object(perfile, 'Directive')
        func = mocker.Mock(__name__='test_func')

        decorator = ParserForTest.directive(name='direct')

        assert callable(decorator)
        assert ParserForTest.DIRECTIVES == {}
        assert not mock_Directive.called

        result = decorator(func)

        assert result == func
        assert ParserForTest.DIRECTIVES == {
            'direct': mock_Directive.return_value,
        }
        mock_Directive.assert_called_once_with(
            'direct', 'direct', perfile._unset, func
        )
        assert not func.called

    def test_directive_all_args(self, mocker):
        mocker.patch.dict(ParserForTest.DIRECTIVES)
        mock_Directive = mocker.patch.object(perfile, 'Directive')
        func = mocker.Mock(__name__='test_func')

        decorator = ParserForTest.directive('init', 'direct', 'key')

        assert callable(decorator)
        assert ParserForTest.DIRECTIVES == {}
        assert not mock_Directive.called

        result = decorator(func)

        assert result == func
        assert ParserForTest.DIRECTIVES == {
            'direct': mock_Directive.return_value,
        }
        mock_Directive.assert_called_once_with(
            'direct', 'key', 'init', func
        )
        assert not func.called

    def test_values(self, mocker):
        directives = {
            'd1': mocker.Mock(init='init', value='d1v'),
            'd2': mocker.Mock(init=perfile._unset, value='d2v'),
            'd3': mocker.Mock(init='init', value='d3v'),
            'd4': mocker.Mock(init=perfile._unset, value='d4v'),
        }
        mocker.patch.dict(ParserForTest.DIRECTIVES, directives)

        result = ParserForTest._values()

        assert result == {
            'd1v': directives['d1'].initial.return_value,
            'd3v': directives['d3'].initial.return_value,
        }
        directives['d1'].initial.assert_called_once_with()
        assert not directives['d2'].initial.called
        directives['d3'].initial.assert_called_once_with()
        assert not directives['d4'].initial.called

    def test_init(self):
        result = ParserForTest()

        assert result._deferred is None
        assert result._buf is None
        assert result._comment_pfx is None
        assert result._continued is None
        assert result._start_coord is None
        assert result._lines == 0

    def test_parse_directive_base(self, mocker):
        # Note: reversed() always returns an iterator, whereas range()
        # may not
        mock_tokenize = mocker.patch.object(
            ParserForTest, '_tokenize', return_value=reversed(range(3))
        )
        obj = ParserForTest()
        text = '%simple directive'
        expected = 'simple directive'

        result = obj._parse_directive('coord', text)

        assert obj._comment_pfx is None
        assert obj._continued is None
        assert obj._start_coord is None
        assert result == ('coord', [2, 1, 0])
        mock_tokenize.assert_called_once_with(expected, 'coord')

    def test_parse_directive_with_continued(self, mocker):
        # Note: reversed() always returns an iterator, whereas range()
        # may not
        mock_tokenize = mocker.patch.object(
            ParserForTest, '_tokenize', return_value=reversed(range(3))
        )
        obj = ParserForTest()
        obj._continued = '%simple'
        obj._start_coord = 'start'
        text = 'directive'
        expected = 'simple directive'

        result = obj._parse_directive('coord', text)

        assert obj._comment_pfx is None
        assert obj._continued is None
        assert obj._start_coord is None
        assert result == ('start', [2, 1, 0])
        mock_tokenize.assert_called_once_with(expected, 'start')

    def test_parse_directive_with_comment_pfx(self, mocker):
        # Note: reversed() always returns an iterator, whereas range()
        # may not
        mock_tokenize = mocker.patch.object(
            ParserForTest, '_tokenize', return_value=reversed(range(3))
        )
        obj = ParserForTest()
        obj._comment_pfx = '%simple'
        obj._start_coord = 'start'
        text = '*/directive'
        expected = 'simple directive'

        result = obj._parse_directive('coord', text)

        assert obj._comment_pfx is None
        assert obj._continued is None
        assert obj._start_coord is None
        assert result == ('start', [2, 1, 0])
        mock_tokenize.assert_called_once_with(expected, 'start')

    def test_parse_directive_with_comment_pfx_continued(self, mocker):
        # Note: reversed() always returns an iterator, whereas range()
        # may not
        mock_tokenize = mocker.patch.object(
            ParserForTest, '_tokenize', return_value=reversed(range(3))
        )
        obj = ParserForTest()
        obj._comment_pfx = '%simple'
        obj._start_coord = 'start'
        text = 'directive'

        with pytest.raises(perfile.Continue):
            obj._parse_directive('coord', text)

        assert obj._comment_pfx == '%simple'
        assert obj._continued is None
        assert obj._start_coord == 'start'
        assert not mock_tokenize.called

    def test_parse_directive_double_slash_comment(self, mocker):
        # Note: reversed() always returns an iterator, whereas range()
        # may not
        mock_tokenize = mocker.patch.object(
            ParserForTest, '_tokenize', return_value=reversed(range(3))
        )
        obj = ParserForTest()
        text = '%simple directive // some comment'
        expected = 'simple directive'

        result = obj._parse_directive('coord', text)

        assert obj._comment_pfx is None
        assert obj._continued is None
        assert obj._start_coord is None
        assert result == ('coord', [2, 1, 0])
        mock_tokenize.assert_called_once_with(expected, 'coord')

    def test_parse_directive_one_line_c_comment(self, mocker):
        # Note: reversed() always returns an iterator, whereas range()
        # may not
        mock_tokenize = mocker.patch.object(
            ParserForTest, '_tokenize', return_value=reversed(range(3))
        )
        obj = ParserForTest()
        text = '%simple/* some comment */directive'
        expected = 'simple directive'

        result = obj._parse_directive('coord', text)

        assert obj._comment_pfx is None
        assert obj._continued is None
        assert obj._start_coord is None
        assert result == ('coord', [2, 1, 0])
        mock_tokenize.assert_called_once_with(expected, 'coord')

    def test_parse_directive_one_line_c_comment_multi(self, mocker):
        # Note: reversed() always returns an iterator, whereas range()
        # may not
        mock_tokenize = mocker.patch.object(
            ParserForTest, '_tokenize', return_value=reversed(range(3))
        )
        obj = ParserForTest()
        text = '%simple/* some */directive/**/test'
        expected = 'simple directive test'

        result = obj._parse_directive('coord', text)

        assert obj._comment_pfx is None
        assert obj._continued is None
        assert obj._start_coord is None
        assert result == ('coord', [2, 1, 0])
        mock_tokenize.assert_called_once_with(expected, 'coord')

    def test_parse_directive_multi_line_c_comment(self, mocker):
        # Note: reversed() always returns an iterator, whereas range()
        # may not
        mock_tokenize = mocker.patch.object(
            ParserForTest, '_tokenize', return_value=reversed(range(3))
        )
        obj = ParserForTest()
        text = '%simple directive /* Multi-line comment'

        with pytest.raises(perfile.Continue):
            obj._parse_directive('coord', text)

        assert obj._comment_pfx == '%simple directive '
        assert obj._continued is None
        assert obj._start_coord is 'coord'
        assert not mock_tokenize.called

    def test_parse_directive_multi_line_c_comment_altstart(self, mocker):
        # Note: reversed() always returns an iterator, whereas range()
        # may not
        mock_tokenize = mocker.patch.object(
            ParserForTest, '_tokenize', return_value=reversed(range(3))
        )
        obj = ParserForTest()
        obj._start_coord = 'start'
        text = '%simple directive /* Multi-line comment'

        with pytest.raises(perfile.Continue):
            obj._parse_directive('coord', text)

        assert obj._comment_pfx == '%simple directive '
        assert obj._continued is None
        assert obj._start_coord is 'start'
        assert not mock_tokenize.called

    def test_parse_directive_empty(self, mocker):
        # Note: reversed() always returns an iterator, whereas range()
        # may not
        mock_tokenize = mocker.patch.object(
            ParserForTest, '_tokenize', return_value=reversed(range(3))
        )
        obj = ParserForTest()
        text = '    '

        with pytest.raises(perfile.Continue):
            obj._parse_directive('coord', text)

        assert obj._comment_pfx is None
        assert obj._continued is None
        assert obj._start_coord is None
        assert not mock_tokenize.called

    def test_parse_directive_continuation(self, mocker):
        # Note: reversed() always returns an iterator, whereas range()
        # may not
        mock_tokenize = mocker.patch.object(
            ParserForTest, '_tokenize', return_value=reversed(range(3))
        )
        obj = ParserForTest()
        text = '%simple directive \ '

        with pytest.raises(perfile.Continue):
            obj._parse_directive('coord', text)

        assert obj._comment_pfx is None
        assert obj._continued == '%simple directive '
        assert obj._start_coord == 'coord'
        assert not mock_tokenize.called

    def test_parse_directive_continuation_altstart(self, mocker):
        # Note: reversed() always returns an iterator, whereas range()
        # may not
        mock_tokenize = mocker.patch.object(
            ParserForTest, '_tokenize', return_value=reversed(range(3))
        )
        obj = ParserForTest()
        obj._start_coord = 'start'
        text = '%simple directive \ '

        with pytest.raises(perfile.Continue):
            obj._parse_directive('coord', text)

        assert obj._comment_pfx is None
        assert obj._continued == '%simple directive '
        assert obj._start_coord == 'start'
        assert not mock_tokenize.called

    def test_parse_directive_bad_directive(self, mocker):
        # Note: reversed() always returns an iterator, whereas range()
        # may not
        mock_tokenize = mocker.patch.object(
            ParserForTest, '_tokenize', return_value=reversed(range(3))
        )
        obj = ParserForTest()
        text = 'simple directive'

        with pytest.raises(perfile.ParseException):
            obj._parse_directive('coord', text)

        assert obj._comment_pfx is None
        assert obj._continued is None
        assert obj._start_coord is None
        assert not mock_tokenize.called

    def test_parse_line_start_base(self, mocker):
        directive = mocker.Mock(return_value=None)
        mocker.patch.dict(ParserForTest.DIRECTIVES, directive=directive)
        mock_parse_directive = mocker.patch.object(
            ParserForTest,
            '_parse_directive',
            return_value=(
                'start',
                [perfile.Token(perfile.TOK_WORD, 'directive'), 2, 3]
            )
        )
        mock_LineList = mocker.patch.object(perfile.linelist, 'LineList')
        obj = ParserForTest()

        obj._parse_line('coord', '%test directive', 'values')

        assert obj._lines == 1
        assert obj._deferred is None
        assert obj._buf is None
        mock_parse_directive.assert_called_once_with(
            'coord', '%test directive'
        )
        directive.assert_called_once_with('values', 'start', [2, 3])
        assert not mock_LineList.called

    def test_parse_line_start_deferred(self, mocker):
        directive = mocker.Mock(return_value='deferred')
        mocker.patch.dict(ParserForTest.DIRECTIVES, directive=directive)
        mock_parse_directive = mocker.patch.object(
            ParserForTest,
            '_parse_directive',
            return_value=(
                'start',
                [perfile.Token(perfile.TOK_WORD, 'directive'), 2, 3]
            )
        )
        mock_LineList = mocker.patch.object(perfile.linelist, 'LineList')
        obj = ParserForTest()

        obj._parse_line('coord', '%test directive', 'values')

        assert obj._lines == 1
        assert obj._deferred == 'deferred'
        assert obj._buf == mock_LineList.return_value
        mock_parse_directive.assert_called_once_with(
            'coord', '%test directive'
        )
        directive.assert_called_once_with('values', 'start', [2, 3])
        mock_LineList.assert_called_once_with()

    def test_parse_line_start_bad_type(self, mocker):
        directive = mocker.Mock(return_value=None)
        mocker.patch.dict(ParserForTest.DIRECTIVES, directive=directive)
        mock_parse_directive = mocker.patch.object(
            ParserForTest,
            '_parse_directive',
            return_value=(
                'start',
                [perfile.Token(perfile.TOK_STR, 'directive'), 2, 3]
            )
        )
        mock_LineList = mocker.patch.object(perfile.linelist, 'LineList')
        obj = ParserForTest()

        with pytest.raises(perfile.ParseException):
            obj._parse_line('coord', '%test directive', 'values')

        assert obj._lines == 1
        assert obj._deferred is None
        assert obj._buf is None
        mock_parse_directive.assert_called_once_with(
            'coord', '%test directive'
        )
        assert not directive.called
        assert not mock_LineList.called

    def test_parse_line_start_bad_directive(self, mocker):
        directive = mocker.Mock(return_value=None)
        mocker.patch.dict(ParserForTest.DIRECTIVES, directive=directive)
        mock_parse_directive = mocker.patch.object(
            ParserForTest,
            '_parse_directive',
            return_value=(
                'start',
                [perfile.Token(perfile.TOK_WORD, 'spam'), 2, 3]
            )
        )
        mock_LineList = mocker.patch.object(perfile.linelist, 'LineList')
        obj = ParserForTest()

        with pytest.raises(perfile.ParseException):
            obj._parse_line('coord', '%test directive', 'values')

        assert obj._lines == 1
        assert obj._deferred is None
        assert obj._buf is None
        mock_parse_directive.assert_called_once_with(
            'coord', '%test directive'
        )
        assert not directive.called
        assert not mock_LineList.called

    def test_parse_line_end_base(self, mocker):
        deferred = mocker.Mock(return_value=None)
        mock_parse_directive = mocker.patch.object(
            ParserForTest,
            '_parse_directive',
            return_value=(
                'start',
                [perfile.Token(perfile.TOK_CHAR, '}'), 2, 3]
            )
        )
        mock_LineList = mocker.patch.object(perfile.linelist, 'LineList')
        obj = ParserForTest()
        obj._deferred = deferred
        obj._buf = 'buf'

        obj._parse_line('coord', '%} end directive', 'values')

        assert obj._lines == 1
        assert obj._deferred is None
        assert obj._buf is None
        mock_parse_directive.assert_called_once_with(
            'coord', '%} end directive'
        )
        deferred.assert_called_once_with('start', 'buf', [2, 3])
        assert not mock_LineList.called

    def test_parse_line_end_deferred(self, mocker):
        deferred = mocker.Mock(return_value='deferred')
        mock_parse_directive = mocker.patch.object(
            ParserForTest,
            '_parse_directive',
            return_value=(
                'start',
                [perfile.Token(perfile.TOK_CHAR, '}'), 2, 3]
            )
        )
        mock_LineList = mocker.patch.object(perfile.linelist, 'LineList')
        obj = ParserForTest()
        obj._deferred = deferred
        obj._buf = 'buf'

        obj._parse_line('coord', '%} end directive', 'values')

        assert obj._lines == 1
        assert obj._deferred == 'deferred'
        assert obj._buf == mock_LineList.return_value
        mock_parse_directive.assert_called_once_with(
            'coord', '%} end directive'
        )
        deferred.assert_called_once_with('start', 'buf', [2, 3])
        mock_LineList.assert_called_once_with()

    def test_parse_line_end_comment_pfx(self, mocker):
        deferred = mocker.Mock(return_value=None)
        mock_parse_directive = mocker.patch.object(
            ParserForTest,
            '_parse_directive',
            return_value=(
                'start',
                [perfile.Token(perfile.TOK_CHAR, '}'), 2, 3]
            )
        )
        mock_LineList = mocker.patch.object(perfile.linelist, 'LineList')
        obj = ParserForTest()
        obj._deferred = deferred
        obj._buf = 'buf'
        obj._comment_pfx = '%'

        obj._parse_line('coord', '} end directive', 'values')

        assert obj._lines == 1
        assert obj._deferred is None
        assert obj._buf is None
        mock_parse_directive.assert_called_once_with(
            'coord', '} end directive'
        )
        deferred.assert_called_once_with('start', 'buf', [2, 3])
        assert not mock_LineList.called

    def test_parse_line_end_continued(self, mocker):
        deferred = mocker.Mock(return_value=None)
        mock_parse_directive = mocker.patch.object(
            ParserForTest,
            '_parse_directive',
            return_value=(
                'start',
                [perfile.Token(perfile.TOK_CHAR, '}'), 2, 3]
            )
        )
        mock_LineList = mocker.patch.object(perfile.linelist, 'LineList')
        obj = ParserForTest()
        obj._deferred = deferred
        obj._buf = 'buf'
        obj._continued = '%'

        obj._parse_line('coord', '} end directive', 'values')

        assert obj._lines == 1
        assert obj._deferred is None
        assert obj._buf is None
        mock_parse_directive.assert_called_once_with(
            'coord', '} end directive'
        )
        deferred.assert_called_once_with('start', 'buf', [2, 3])
        assert not mock_LineList.called

    def test_parse_line_end_bad_close(self, mocker):
        deferred = mocker.Mock(return_value=None)
        mock_parse_directive = mocker.patch.object(
            ParserForTest,
            '_parse_directive',
            return_value=(
                'start',
                [perfile.Token(perfile.TOK_CHAR, ')'), 2, 3]
            )
        )
        mock_LineList = mocker.patch.object(perfile.linelist, 'LineList')
        obj = ParserForTest()
        obj._deferred = deferred
        obj._buf = 'buf'

        with pytest.raises(perfile.ParseException):
            obj._parse_line('coord', '%} end directive', 'values')

        assert obj._lines == 1
        assert obj._deferred == deferred
        assert obj._buf == 'buf'
        mock_parse_directive.assert_called_once_with(
            'coord', '%} end directive'
        )
        assert not deferred.called
        assert not mock_LineList.called

    def test_parse_line_accumulate_base(self, mocker):
        buf = mocker.Mock()
        deferred = mocker.Mock(return_value=None)
        mock_parse_directive = mocker.patch.object(
            ParserForTest,
            '_parse_directive',
            return_value=(
                'start',
                [perfile.Token(perfile.TOK_CHAR, '}'), 2, 3]
            )
        )
        mock_LineList = mocker.patch.object(perfile.linelist, 'LineList')
        obj = ParserForTest()
        obj._deferred = deferred
        obj._buf = buf

        obj._parse_line('coord', '} new line  ', 'values')

        assert obj._lines == 1
        assert obj._deferred == deferred
        assert obj._buf == buf
        assert not mock_parse_directive.called
        assert not deferred.called
        assert not mock_LineList.called
        buf.append.assert_called_once_with('} new line  ', 'coord')

    def test_parse_line_accumulate_newline(self, mocker):
        buf = mocker.Mock()
        deferred = mocker.Mock(return_value=None)
        mock_parse_directive = mocker.patch.object(
            ParserForTest,
            '_parse_directive',
            return_value=(
                'start',
                [perfile.Token(perfile.TOK_CHAR, '}'), 2, 3]
            )
        )
        mock_LineList = mocker.patch.object(perfile.linelist, 'LineList')
        obj = ParserForTest()
        obj._deferred = deferred
        obj._buf = buf

        obj._parse_line('coord', '} new line  \n', 'values')

        assert obj._lines == 1
        assert obj._deferred == deferred
        assert obj._buf == buf
        assert not mock_parse_directive.called
        assert not deferred.called
        assert not mock_LineList.called
        buf.append.assert_called_once_with('} new line  ', 'coord')

    def test_parse_base(self, mocker):
        lines = [
            'line 1',
            'line 2',
            'continue',
            'line 4',
            'continue',
            'line 6',
        ]
        stream = six.StringIO('\n'.join(lines) + '\n')
        stream.name = 'stream'
        mock_values = mocker.patch.object(ParserForTest, '_values')
        mock_Coordinate = mocker.patch.object(
            perfile.location,
            'Coordinate',
            side_effect=lambda x, y: '%s-%d' % (x, y),
        )
        mock_parse_line = mocker.patch.object(
            ParserForTest, '_parse_line', side_effect=_fake_parse_line
        )
        obj = ParserForTest()

        obj.parse(stream)

        mock_values.assert_called_once_with()
        Coordinate_expected = [
            mocker.call('stream', i + 1) for i in range(len(lines))
        ]
        mock_Coordinate.assert_has_calls(Coordinate_expected)
        assert mock_Coordinate.call_count == len(Coordinate_expected)
        mock_parse_line_expected = [
            mocker.call(
                'stream-%d' % (i + 1), '%s\n' % line, mock_values.return_value
            )
            for i, line in enumerate(lines)
        ]
        mock_parse_line.assert_has_calls(mock_parse_line_expected)
        assert mock_parse_line.call_count == len(mock_parse_line_expected)

    def test_parse_path(self, mocker):
        lines = [
            'line 1',
            'line 2',
            'continue',
            'line 4',
            'continue',
            'line 6',
        ]
        stream = six.StringIO('\n'.join(lines) + '\n')
        stream.name = 'stream'
        mock_values = mocker.patch.object(ParserForTest, '_values')
        mock_Coordinate = mocker.patch.object(
            perfile.location,
            'Coordinate',
            side_effect=lambda x, y: '%s-%d' % (x, y),
        )
        mock_parse_line = mocker.patch.object(
            ParserForTest, '_parse_line', side_effect=_fake_parse_line
        )
        obj = ParserForTest()

        obj.parse(stream, 'path')

        mock_values.assert_called_once_with()
        Coordinate_expected = [
            mocker.call('path', i + 1) for i in range(len(lines))
        ]
        mock_Coordinate.assert_has_calls(Coordinate_expected)
        assert mock_Coordinate.call_count == len(Coordinate_expected)
        mock_parse_line_expected = [
            mocker.call(
                'path-%d' % (i + 1), '%s\n' % line, mock_values.return_value
            )
            for i, line in enumerate(lines)
        ]
        mock_parse_line.assert_has_calls(mock_parse_line_expected)
        assert mock_parse_line.call_count == len(mock_parse_line_expected)

    def test_parse_hanging_continuation(self, mocker):
        lines = [
            'line 1',
            'line 2',
            'continue',
            'line 4',
            'continue',
            'line 6',
        ]
        stream = six.StringIO('\n'.join(lines) + '\n')
        stream.name = 'stream'
        mock_values = mocker.patch.object(ParserForTest, '_values')
        mock_Coordinate = mocker.patch.object(
            perfile.location,
            'Coordinate',
            side_effect=lambda x, y: '%s-%d' % (x, y),
        )
        mock_parse_line = mocker.patch.object(
            ParserForTest, '_parse_line', side_effect=_fake_parse_line
        )
        obj = ParserForTest()
        obj._continued = 'fragment'

        with pytest.raises(perfile.ParseException):
            obj.parse(stream)

        mock_values.assert_called_once_with()
        Coordinate_expected = [
            mocker.call('stream', i + 1) for i in range(len(lines))
        ]
        mock_Coordinate.assert_has_calls(Coordinate_expected)
        assert mock_Coordinate.call_count == len(Coordinate_expected)
        mock_parse_line_expected = [
            mocker.call(
                'stream-%d' % (i + 1), '%s\n' % line, mock_values.return_value
            )
            for i, line in enumerate(lines)
        ]
        mock_parse_line.assert_has_calls(mock_parse_line_expected)
        assert mock_parse_line.call_count == len(mock_parse_line_expected)

    def test_parse_hanging_comment(self, mocker):
        lines = [
            'line 1',
            'line 2',
            'continue',
            'line 4',
            'continue',
            'line 6',
        ]
        stream = six.StringIO('\n'.join(lines) + '\n')
        stream.name = 'stream'
        mock_values = mocker.patch.object(ParserForTest, '_values')
        mock_Coordinate = mocker.patch.object(
            perfile.location,
            'Coordinate',
            side_effect=lambda x, y: '%s-%d' % (x, y),
        )
        mock_parse_line = mocker.patch.object(
            ParserForTest, '_parse_line', side_effect=_fake_parse_line
        )
        obj = ParserForTest()
        obj._comment_pfx = 'fragment'

        with pytest.raises(perfile.ParseException):
            obj.parse(stream)

        mock_values.assert_called_once_with()
        Coordinate_expected = [
            mocker.call('stream', i + 1) for i in range(len(lines))
        ]
        mock_Coordinate.assert_has_calls(Coordinate_expected)
        assert mock_Coordinate.call_count == len(Coordinate_expected)
        mock_parse_line_expected = [
            mocker.call(
                'stream-%d' % (i + 1), '%s\n' % line, mock_values.return_value
            )
            for i, line in enumerate(lines)
        ]
        mock_parse_line.assert_has_calls(mock_parse_line_expected)
        assert mock_parse_line.call_count == len(mock_parse_line_expected)

    def test_parse_hanging_directive(self, mocker):
        lines = [
            'line 1',
            'line 2',
            'continue',
            'line 4',
            'continue',
            'line 6',
        ]
        stream = six.StringIO('\n'.join(lines) + '\n')
        stream.name = 'stream'
        mock_values = mocker.patch.object(ParserForTest, '_values')
        mock_Coordinate = mocker.patch.object(
            perfile.location,
            'Coordinate',
            side_effect=lambda x, y: '%s-%d' % (x, y),
        )
        mock_parse_line = mocker.patch.object(
            ParserForTest, '_parse_line', side_effect=_fake_parse_line
        )
        obj = ParserForTest()
        deferred = mocker.Mock()
        obj._deferred = deferred
        obj._buf = 'buf'

        with pytest.raises(perfile.ParseException):
            obj.parse(stream)

        mock_values.assert_called_once_with()
        Coordinate_expected = [
            mocker.call('stream', i + 1) for i in range(len(lines))
        ] + [mocker.call('stream', 0)]  # _lines not updated by _parse_line()
        mock_Coordinate.assert_has_calls(Coordinate_expected)
        assert mock_Coordinate.call_count == len(Coordinate_expected)
        mock_parse_line_expected = [
            mocker.call(
                'stream-%d' % (i + 1), '%s\n' % line, mock_values.return_value
            )
            for i, line in enumerate(lines)
        ]
        mock_parse_line.assert_has_calls(mock_parse_line_expected)
        assert mock_parse_line.call_count == len(mock_parse_line_expected)
        deferred.assert_called_once_with('stream-0', 'buf', None)
