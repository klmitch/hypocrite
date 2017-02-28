from hypocrite import location

other = object()


class TestCoordinate(object):
    def test_init(self):
        result = location.Coordinate('file.name', 23)

        assert result.path == 'file.name'
        assert result.lno == 23

    def test_str(self):
        obj = location.Coordinate('file.name', 23)

        result = str(obj)

        assert result == 'file.name:23'

    def test_eq_equal(self):
        obj1 = location.Coordinate('file.name', 23)
        obj2 = location.Coordinate('file.name', 23)

        assert obj1.__eq__(obj2)

    def test_eq_unequal_line(self):
        obj1 = location.Coordinate('file.name', 23)
        obj2 = location.Coordinate('file.name', 42)

        assert not obj1.__eq__(obj2)

    def test_eq_unequal_file(self):
        obj1 = location.Coordinate('file.name', 23)
        obj2 = location.Coordinate('other.name', 23)

        assert not obj1.__eq__(obj2)

    def test_eq_other(self):
        obj = location.Coordinate('file.name', 23)

        assert not obj.__eq__(other)

    def test_ne_equal(self):
        obj1 = location.Coordinate('file.name', 23)
        obj2 = location.Coordinate('file.name', 23)

        assert not obj1.__ne__(obj2)

    def test_ne_unequal_line(self):
        obj1 = location.Coordinate('file.name', 23)
        obj2 = location.Coordinate('file.name', 42)

        assert obj1.__ne__(obj2)

    def test_ne_unequal_file(self):
        obj1 = location.Coordinate('file.name', 23)
        obj2 = location.Coordinate('other.name', 23)

        assert obj1.__ne__(obj2)

    def test_ne_other(self):
        obj = location.Coordinate('file.name', 23)

        assert obj.__ne__(other)

    def test_add_integer(self):
        obj = location.Coordinate('file.name', 23)

        result = obj.__add__(3)

        assert result is not obj
        assert isinstance(result, location.Coordinate)
        assert result.path == obj.path
        assert result.lno == obj.lno + 3

    def test_add_other(self):
        obj = location.Coordinate('file.name', 23)

        result = obj.__add__(other)

        assert result is NotImplemented

    def test_sub_integer(self, mocker):
        mock_CoordinateRange = mocker.patch.object(location, 'CoordinateRange')
        obj = location.Coordinate('file.name', 23)

        result = obj.__sub__(3)

        assert result is not obj
        assert isinstance(result, location.Coordinate)
        assert result.path == obj.path
        assert result.lno == obj.lno - 3
        assert not mock_CoordinateRange.called

    def test_sub_coordinate_later(self, mocker):
        mock_CoordinateRange = mocker.patch.object(location, 'CoordinateRange')
        obj1 = location.Coordinate('file.name', 23)
        obj2 = location.Coordinate('file.name', 42)

        result = obj1.__sub__(obj2)

        assert result == mock_CoordinateRange.return_value
        mock_CoordinateRange.assert_called_once_with('file.name', 23, 42)

    def test_sub_coordinate_earlier(self, mocker):
        mock_CoordinateRange = mocker.patch.object(location, 'CoordinateRange')
        obj1 = location.Coordinate('file.name', 42)
        obj2 = location.Coordinate('file.name', 23)

        result = obj1.__sub__(obj2)

        assert result == mock_CoordinateRange.return_value
        mock_CoordinateRange.assert_called_once_with('file.name', 23, 42)

    def test_sub_coordinate_badpath(self, mocker):
        mock_CoordinateRange = mocker.patch.object(location, 'CoordinateRange')
        obj1 = location.Coordinate('file.name', 23)
        obj2 = location.Coordinate('other.name', 42)

        result = obj1.__sub__(obj2)

        assert result is NotImplemented
        assert not mock_CoordinateRange.called

    def test_sub_other(self, mocker):
        mock_CoordinateRange = mocker.patch.object(location, 'CoordinateRange')
        obj = location.Coordinate('file.name', 23)

        result = obj.__sub__(other)

        assert result is NotImplemented
        assert not mock_CoordinateRange.called

    def test_line(self, mocker):
        obj = location.Coordinate('file.name', 23)

        assert obj.line == '#line 23 "file.name"'


class TestCoordinateRange(object):
    def test_init(self):
        result = location.CoordinateRange('file.name', 23, 42)

        assert result.path == 'file.name'
        assert result.start == 23
        assert result.end == 42

    def test_str_oneline(self):
        obj = location.CoordinateRange('file.name', 23, 23)

        result = str(obj)

        assert result == 'file.name:23'

    def test_str_multiline(self):
        obj = location.CoordinateRange('file.name', 23, 42)

        result = str(obj)

        assert result == 'file.name:23-42'

    def test_eq_equal(self):
        obj1 = location.CoordinateRange('file.name', 23, 42)
        obj2 = location.CoordinateRange('file.name', 23, 42)

        assert obj1.__eq__(obj2)

    def test_eq_unequal_path(self):
        obj1 = location.CoordinateRange('file.name', 23, 42)
        obj2 = location.CoordinateRange('other.name', 23, 42)

        assert not obj1.__eq__(obj2)

    def test_eq_unequal_start(self):
        obj1 = location.CoordinateRange('file.name', 23, 42)
        obj2 = location.CoordinateRange('file.name', 24, 42)

        assert not obj1.__eq__(obj2)

    def test_eq_unequal_end(self):
        obj1 = location.CoordinateRange('file.name', 23, 42)
        obj2 = location.CoordinateRange('file.name', 23, 43)

        assert not obj1.__eq__(obj2)

    def test_eq_other(self):
        obj = location.CoordinateRange('file.name', 23, 42)

        assert not obj.__eq__(other)

    def test_ne_equal(self):
        obj1 = location.CoordinateRange('file.name', 23, 42)
        obj2 = location.CoordinateRange('file.name', 23, 42)

        assert not obj1.__ne__(obj2)

    def test_ne_unequal_path(self):
        obj1 = location.CoordinateRange('file.name', 23, 42)
        obj2 = location.CoordinateRange('other.name', 23, 42)

        assert obj1.__ne__(obj2)

    def test_ne_unequal_start(self):
        obj1 = location.CoordinateRange('file.name', 23, 42)
        obj2 = location.CoordinateRange('file.name', 24, 42)

        assert obj1.__ne__(obj2)

    def test_ne_unequal_end(self):
        obj1 = location.CoordinateRange('file.name', 23, 42)
        obj2 = location.CoordinateRange('file.name', 23, 43)

        assert obj1.__ne__(obj2)

    def test_ne_other(self):
        obj = location.CoordinateRange('file.name', 23, 42)

        assert obj.__ne__(other)
