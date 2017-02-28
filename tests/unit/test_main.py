from six.moves import builtins

from hypocrite import main


class TestMain(object):
    def test_base(self, mocker):
        mock_parse = mocker.patch.object(main.hypofile.HypoFile, 'parse')
        handle = mocker.MagicMock()
        handle.__enter__.return_value = handle
        mock_open = mocker.patch.object(builtins, 'open', return_value=handle)

        main.main('infile.hypo')

        mock_parse.assert_called_once_with('infile.hypo')
        hfile = mock_parse.return_value
        hfile.render.assert_called_once_with('infile')
        mock_open.assert_called_once_with('infile.c', 'w')
        output = hfile.render.return_value
        output.output.assert_called_once_with(handle, 'infile.c')

    def test_outfile(self, mocker):
        mock_parse = mocker.patch.object(main.hypofile.HypoFile, 'parse')
        handle = mocker.MagicMock()
        handle.__enter__.return_value = handle
        mock_open = mocker.patch.object(builtins, 'open', return_value=handle)

        main.main('infile.hypo', 'outfile.x')

        mock_parse.assert_called_once_with('infile.hypo')
        hfile = mock_parse.return_value
        hfile.render.assert_called_once_with('outfile')
        mock_open.assert_called_once_with('outfile.x', 'w')
        output = hfile.render.return_value
        output.output.assert_called_once_with(handle, 'outfile.x')
