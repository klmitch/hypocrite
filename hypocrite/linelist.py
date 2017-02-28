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

from __future__ import print_function

import collections
import os

# Since entry binding coordinate to a line
_Entry = collections.namedtuple('_Entry', ['coord', 'text'])


class LineList(object):
    """
    A class describing a list-like object that stores text lines,
    along with the coordinate at which those text lines originated.
    Unlike Python lists, objects of this type can only be extended,
    not modified.
    """

    def __init__(self, lines=None, coord=None):
        """
        Initialize a ``LineList`` instance.

        :param list lines: A list of text lines.  Optional.
        :param coord: The coordinate of the first line.  If not
                      provided, ``None`` will be recorded.  This
                      argument is ignored if ``lines`` is not given.
        :type coord: ``hypocrite.location.Coordinate``
        """

        self._entries = [
            _Entry(coord + i if coord is not None else None, line)
            for i, line in enumerate(lines or [])
        ]

    def __len__(self):
        """
        Retrieve the number of lines in the list.

        :returns: The number of lines contained in the list.
        :rtype: ``int``
        """

        return len(self._entries)

    def __getitem__(self, idx):
        """
        Retrieve the lines at a given index.

        :param int idx: The index from which to retrieve the line.

        :returns: The line at that index.
        :rtype: ``str``
        """

        # If given a slice, extract only the text
        if isinstance(idx, slice):
            return [e.text for e in self._entries[idx]]
        else:
            return self._entries[idx].text

    def __iter__(self):
        """
        Iterate over the lines in the list.

        :returns: An iterator that yields each line in turn.
        """

        for entry in self._entries:
            yield entry.text

    def __add__(self, other):
        """
        Add together two ``LineList`` instances.

        :param other: Another ``LineList`` instance.  A bare ``list``
                      is also recognized, but the coordinates of the
                      new entries will be set to ``None``.

        :returns: A new ``LineList`` instance containing the lines
                  from this instance and from ``other``.
        """

        if isinstance(other, LineList):
            new = self.__class__()
            new._entries = self._entries + other._entries
            return new
        elif isinstance(other, list):
            new = self.__class__()
            new._entries = self._entries[:]
            new.extend(other)
            return new

        return NotImplemented

    def __iadd__(self, other):
        """
        Add a ``LineList`` instance to this list.

        :param other: Another ``LineList`` instance.  A bare ``list``
                      is also recognized, but the coordinates of the
                      new entries will be set to ``None``.

        :returns: This ``LineList`` instance, with the additional
                  lines appended.
        """

        if isinstance(other, LineList):
            self._entries += other._entries
            return self
        elif isinstance(other, list):
            self.extend(other)
            return self

        return NotImplemented

    def append(self, line, coord=None):
        """
        Append a new line to the ``LineList`` instance.

        :param str line: The line to append.
        :param coord: The coordinate of the new line.  Defaults to
                      ``None``.
        :type coord: ``hypocrite.location.Coordinate``
        """

        self._entries.append(_Entry(coord, line))

    def extend(self, lines, coord=None):
        """
        Add multiple new lines to the ``LineList`` instance.

        :param list lines: A list of the lines to append.
        :param coord: The coordinate of the first new line.  Defaults
                      to ``None``.
        :type coord: ``hypocrite.location.Coordinate``
        """

        self._entries.extend(
            _Entry(coord + i if coord is not None else None, line)
            for i, line in enumerate(lines)
        )

    def iter_coord(self):
        """
        Iterate over both the text and the associated coordinates.

        :returns: An iterator that yields 2-element tuples; the first
                  element is the coordinate (an instance of
                  ``hypocrite.location.Coordinate`` or ``None``), and
                  the second element is the line.
        """

        return iter(self._entries)

    def output(self, stream, path=None):
        """
        Output a ``LineList`` instance to a stream.

        :param stream: A stream, as opened with ``open()``.  The
                       stream should be opened in text writing mode
                       with universal newlines.
        :param str path: The path of the file being written.  If not
                         provided, ``stream.name`` will be used.

        :raises AttributeError:
            The provided ``stream`` has no ``name`` attribute and
            ``path`` was not provided.
        """

        # Determine the path so we can get the base filename
        if not path:
            path = stream.name
        fname = os.path.basename(path)

        # Initialize some state about the current line number and the
        # last coordinate
        line = 1
        last = None

        # Loop through the entries
        for coord, text in self._entries:
            if coord is None:
                if last is not None:
                    # Reset line context to current line number in
                    # the file
                    line += 1
                    print('#line %d "%s"' % (line, fname), file=stream)

                # Both coord and last are None, so line numbering is
                # correct without a #line directive

            elif last is None or last + 1 != coord:
                # Shifting coordinates out-of-band, so emit a #line
                print(coord.line, file=stream)
                line += 1

            # Emit the text and increment the line count
            print(text, file=stream)
            line += 1

            # Keep track of the last coordinate, so we know when to
            # emit #line directives
            last = coord
