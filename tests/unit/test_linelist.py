import six

from hypocrite import linelist
from hypocrite import location

other = object()


class TestLineList(object):
    def test_init_base(self):
        result = linelist.LineList()

        assert result._entries == []

    def test_init_nocoord(self):
        result = linelist.LineList(['l1', 'l2', 'l3'])

        assert result._entries == [
            (None, 'l1'),
            (None, 'l2'),
            (None, 'l3'),
        ]

    def test_init_withcoord(self):
        result = linelist.LineList(['l1', 'l2', 'l3'], 5)

        assert result._entries == [
            (5, 'l1'),
            (6, 'l2'),
            (7, 'l3'),
        ]

    def test_len(self):
        obj = linelist.LineList(['l1', 'l2', 'l3'])

        assert len(obj) == 3

    def test_getitem_base(self):
        obj = linelist.LineList(['l1', 'l2', 'l3'])

        assert obj[1] == 'l2'

    def test_getitem_slice(self):
        obj = linelist.LineList(['l1', 'l2', 'l3', 'l4'])

        assert obj[1:-1] == ['l2', 'l3']

    def test_iter(self):
        obj = linelist.LineList(['l1', 'l2', 'l3'])

        result = list(iter(obj))

        assert result == ['l1', 'l2', 'l3']

    def test_add_linelist(self, mocker):
        mock_extend = mocker.patch.object(linelist.LineList, 'extend')
        obj1 = linelist.LineList(['l1', 'l2', 'l3'], 1)
        obj2 = linelist.LineList(['l4', 'l5', 'l6'])

        result = obj1.__add__(obj2)

        assert result is not obj1
        assert result is not obj2
        assert isinstance(result, linelist.LineList)
        assert result._entries == [
            (1, 'l1'),
            (2, 'l2'),
            (3, 'l3'),
            (None, 'l4'),
            (None, 'l5'),
            (None, 'l6'),
        ]
        assert not mock_extend.called

    def test_add_list(self, mocker):
        mock_extend = mocker.patch.object(linelist.LineList, 'extend')
        obj1 = linelist.LineList(['l1', 'l2', 'l3'], 1)
        obj2 = ['l4', 'l5', 'l6']

        result = obj1.__add__(obj2)

        assert result is not obj1
        assert result is not obj2
        assert isinstance(result, linelist.LineList)
        assert result._entries == [
            (1, 'l1'),
            (2, 'l2'),
            (3, 'l3'),
        ]
        mock_extend.assert_called_once_with(obj2)

    def test_add_other(self, mocker):
        mock_extend = mocker.patch.object(linelist.LineList, 'extend')
        obj = linelist.LineList(['l1', 'l2', 'l3'], 1)

        result = obj.__add__(other)

        assert result is NotImplemented
        assert not mock_extend.called

    def test_iadd_linelist(self, mocker):
        mock_extend = mocker.patch.object(linelist.LineList, 'extend')
        obj1 = linelist.LineList(['l1', 'l2', 'l3'], 1)
        obj2 = linelist.LineList(['l4', 'l5', 'l6'])

        result = obj1.__iadd__(obj2)

        assert result is obj1
        assert result._entries == [
            (1, 'l1'),
            (2, 'l2'),
            (3, 'l3'),
            (None, 'l4'),
            (None, 'l5'),
            (None, 'l6'),
        ]
        assert not mock_extend.called

    def test_iadd_list(self, mocker):
        mock_extend = mocker.patch.object(linelist.LineList, 'extend')
        obj1 = linelist.LineList(['l1', 'l2', 'l3'], 1)
        obj2 = ['l4', 'l5', 'l6']

        result = obj1.__iadd__(obj2)

        assert result is obj1
        assert result._entries == [
            (1, 'l1'),
            (2, 'l2'),
            (3, 'l3'),
        ]
        mock_extend.assert_called_once_with(obj2)

    def test_iadd_other(self, mocker):
        mock_extend = mocker.patch.object(linelist.LineList, 'extend')
        obj = linelist.LineList(['l1', 'l2', 'l3'], 1)

        result = obj.__iadd__(other)

        assert result is NotImplemented
        assert not mock_extend.called

    def test_append_base(self):
        obj = linelist.LineList(['l1', 'l2', 'l3'], 1)

        obj.append('l4')

        assert obj._entries == [
            (1, 'l1'),
            (2, 'l2'),
            (3, 'l3'),
            (None, 'l4'),
        ]

    def test_append_coord(self):
        obj = linelist.LineList(['l1', 'l2', 'l3'], 1)

        obj.append('l4', 18)

        assert obj._entries == [
            (1, 'l1'),
            (2, 'l2'),
            (3, 'l3'),
            (18, 'l4'),
        ]

    def test_extend_base(self):
        obj = linelist.LineList(['l1', 'l2', 'l3'], 1)
        lines = ['l4', 'l5', 'l6']

        obj.extend(lines)

        assert obj._entries == [
            (1, 'l1'),
            (2, 'l2'),
            (3, 'l3'),
            (None, 'l4'),
            (None, 'l5'),
            (None, 'l6'),
        ]

    def test_extend_coord(self):
        obj = linelist.LineList(['l1', 'l2', 'l3'], 1)
        lines = ['l4', 'l5', 'l6']

        obj.extend(lines, 18)

        assert obj._entries == [
            (1, 'l1'),
            (2, 'l2'),
            (3, 'l3'),
            (18, 'l4'),
            (19, 'l5'),
            (20, 'l6'),
        ]

    def test_iter_coord(self):
        obj = linelist.LineList(['l1', 'l2', 'l3'], 1)

        result = list(obj.iter_coord())

        assert result == [
            (1, 'l1'),
            (2, 'l2'),
            (3, 'l3'),
        ]

    def test_output_base(self):
        obj = linelist.LineList(['l1', 'l2', 'l3', 'l4', 'l5'])
        stream = six.StringIO()
        stream.name = 'base.path'

        obj.output(stream, 'other.path')

        assert stream.getvalue() == 'l1\nl2\nl3\nl4\nl5\n'

    def test_output_location_switch(self):
        obj = linelist.LineList(['l1', 'l2', 'l3'])
        obj.extend(['l4', 'l5', 'l6'], location.Coordinate('some.path', 10))
        obj.extend(['l7', 'l8', 'l9'])
        obj.extend(['l10', 'l11', 'l12'], location.Coordinate('my.path', 5))
        stream = six.StringIO()
        stream.name = 'base.path'

        obj.output(stream, 'other.path')

        assert stream.getvalue() == (
            'l1\n'
            'l2\n'
            'l3\n'
            '#line 10 "some.path"\n'
            'l4\n'
            'l5\n'
            'l6\n'
            '#line 9 "other.path"\n'
            'l7\n'
            'l8\n'
            'l9\n'
            '#line 5 "my.path"\n'
            'l10\n'
            'l11\n'
            'l12\n'
        )

    def test_output_location_switch_stream_name(self):
        obj = linelist.LineList(['l1', 'l2', 'l3'])
        obj.extend(['l4', 'l5', 'l6'], location.Coordinate('some.path', 10))
        obj.extend(['l7', 'l8', 'l9'])
        obj.extend(['l10', 'l11', 'l12'], location.Coordinate('my.path', 5))
        stream = six.StringIO()
        stream.name = 'base.path'

        obj.output(stream)

        assert stream.getvalue() == (
            'l1\n'
            'l2\n'
            'l3\n'
            '#line 10 "some.path"\n'
            'l4\n'
            'l5\n'
            'l6\n'
            '#line 9 "base.path"\n'
            'l7\n'
            'l8\n'
            'l9\n'
            '#line 5 "my.path"\n'
            'l10\n'
            'l11\n'
            'l12\n'
        )
