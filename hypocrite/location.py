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

import six


class Coordinate(object):
    """
    Coordinate within a file.
    """

    def __init__(self, path, lno):
        """
        Initialize a ``Coordinate`` instance.

        :param str path: The path to the file.
        :param int lno: The 1-indexed line number within the file.
        """

        self.path = path
        self.lno = lno

    def __str__(self):
        """
        Generate a string representation of the coordinate.  The string
        representation gives the file name and the line number,
        separated by a ':', and is used for error reporting.

        :returns: The string representation of the coordinate.
        """

        return '%s:%d' % (self.path, self.lno)

    def __eq__(self, other):
        """
        Determine if another coordinate is equal to this one.

        :param other: The other object to compare with.

        :returns: A ``True`` value if the coordinates are equal,
                  ``False`` otherwise.
        """

        # If other isn't a Coordinate, they can't be equal
        if not isinstance(other, Coordinate):
            return False

        return self.path == other.path and self.lno == other.lno

    def __ne__(self, other):
        """
        Determine if another coordinate is not equal to this one.

        :param other: The other object to compare with.

        :returns: A ``True`` value if the coordinates are not equal,
                  ``False`` otherwise.
        """

        # If other isn't a Coordinate, they can't be equal
        if not isinstance(other, Coordinate):
            return True

        return self.path != other.path or self.lno != other.lno

    def __add__(self, other):
        """
        Generate a new coordinate offset from this one by a fixed amount.

        :param int other: The amount to offset this coordinate by.

        :returns: A new ``Coordinate`` instance offset by the correct
                  amount.
        """

        if not isinstance(other, six.integer_types):
            # Can't handle that
            return NotImplemented

        return self.__class__(self.path, self.lno + other)

    def __sub__(self, other):
        """
        Either generate a new coordinate offset from this one by a fixed
        amount, or generate coordinate range that covers both this
        coordinate and another.

        :param other: The offset (integer), or another coordinate
                      (instance of ``Coordinate``) to form a range
                      with.  Note that ordering of this operation is
                      not important.

        :returns: Either a ``Coordinate`` instance offset by the
                  correct amount, or a ``CoordinateRange`` instance
                  covering the lines.
        """

        # Handle the offset case first
        if isinstance(other, six.integer_types):
            return self.__class__(self.path, self.lno - other)

        if not isinstance(other, Coordinate) or self.path != other.path:
            # Can't handle that
            return NotImplemented

        # Pick the correct order
        start, end = other.lno, self.lno
        if end < start:
            start, end = end, start

        return CoordinateRange(self.path, start, end)

    @property
    def line(self):
        """
        Retrieve a C preprocessor-style ``#line`` directive representing
        the coordinate.
        """

        return '#line %d "%s"' % (self.lno, self.path)


class CoordinateRange(object):
    """
    A range of coordinates within a file.
    """

    def __init__(self, path, start, end):
        """
        Initialize a ``CoordinateRange`` instance.

        :param str path: The path to the file.
        :param int start: The 1-indexed line number of the first line
                          in the range.
        :param int end: The 1-indexed line number of the last line in
                        the range.
        """

        self.path = path
        self.start = start
        self.end = end

    def __str__(self):
        """
        Generate a string representation of the coordinate range.  The
        string representation gives the file name, followed by a ':',
        followed by the starting and ending line numbers, which are
        joined by a '-'.

        :returns: The string representation of the coordinate range.
        """

        # If start and end are the same, don't include the '-end'
        if self.start == self.end:
            return '%s:%d' % (self.path, self.start)

        return '%s:%d-%d' % (self.path, self.start, self.end)

    def __eq__(self, other):
        """
        Determine if another coordinate range is equal to this one.

        :param other: The other object to compare with.

        :returns: A ``True`` value if the coordinate ranges are equal,
                  ``False`` otherwise.
        """

        # If other isn't a CoordinateRange, they can't be equal
        if not isinstance(other, CoordinateRange):
            return False

        return (self.path == other.path and self.start == other.start and
                self.end == other.end)

    def __ne__(self, other):
        """
        Determine if another coordinate range is not equal to this one.

        :param other: The other object to compare with.

        :returns: A ``True`` value if the coordinate ranges are not
                  equal, ``False`` otherwise.
        """

        # If other isn't a CoordinateRange, they can't be equal
        if not isinstance(other, CoordinateRange):
            return True

        return (self.path != other.path or self.start != other.start or
                self.end != other.end)
