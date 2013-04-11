#!/usr/bin/python3
#-*- coding: utf-8 -*-
# This code is mostly PEP8-compliant. See
# http://www.python.org/dev/peps/pep-0008/.
"""

Wyrd In: Time tracker and task manager
CC-Share Alike 2012 © The Wyrd In team
https://github.com/WyrdIn

This module implements classes related to time definitions.

"""
from datetime import datetime, timedelta

from backend.generic import DBObject


# Constants.
zero_delta = timedelta()


def daystart(dt=lambda: datetime.now(), tz=None):
    return dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=tz)


def dayend(dt=lambda: datetime.now(), tz=None):
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999,
                      tzinfo=tz)


class Interval(object):
    """ Represents a time interval -- not just its length, but also its
    absolute position (start and end times).

    """

    def __init__(self, start=None, end=None):
        """Initialises the object."""
        if (not (start is None or isinstance(start, datetime))
                or not (end is None or isinstance(end, datetime))):
            raise TypeError('The `start\' and `end\' arguments have to '
                            'be a `datetime\' instance or None.')
        if start and end and start > end:
            raise ValueError('Start must be earlier than end.')
        self.start = start
        self.end = end

    def __str__(self):
        return '{start!s}--{end!s}'.format(start=self.start,
                                           end=self.end)

    @property
    def length(self):
        if self.start is None or self.end is None:
            return timedelta.max
        return self.end - self.start

    @length.setter
    def length(self, newlength):
        if self.start is None and self.end is None:
            raise ValueError('Cannot set the length for an unbound interval.')
        if self.start is None:
            self.start = self.end - newlength
        else:
            self.end = self.start + newlength

    def intersects(self, other):
        start_after_other_end = (self.start is not None
                                 and other.end is not None
                                 and self.start > other.end)
        end_before_other_start = (self.end is not None
                                  and other.start is not None
                                  and self.end < other.start)
        return not start_after_other_end and not end_before_other_start

    def includes(self, dt):
        return (self.start is None or self.start <= dt) and \
               (self.end is None or self.end >= dt)

    def iscurrent(self, tz=None):
        if tz is None:
            return self.includes(datetime.now())
        else:
            # XXX This is a workaround, not a principled solution to DST.
            now = datetime.now(tz)
            return self.includes(now + now.dst())


class WorkSlot(Interval, DBObject):
    """ This shall be a time span (or `timedelta' in Python terminology) with
    the annotation saying how it was spent. It shall link to the relevant task
    (or, perhaps, a list of concurrently performed tasks). The annotations
    should include facts like start time, end time, concentration devoted to
    the task (may be in relation to the number of simultaneously performed
    tasks), comments, state of the task before and after this work slot.

    """

    def __init__(self, task, start, end=None, id=None):
        """Creates a new work slot.

        Keyword arguments:
            - task: an instance of task this work slot refers to
            - start: a datetime instance representing the start of this work
                     slot
            - end: a datetime instance representing the end of this work
                   slot (or None, meaning it has not ended yet)
            - id: the ID (a number) of this work slot as a database object, if
                  a specific one is required

        """
        super().__init__(start, end)
        DBObject.__init__(self, id)
        self.task = task

    def __str__(self):
        return "<WorkSlot: {task}, {invl}>".format(
            task=self.task,
            invl=super().__str__())

    def __repr__(self):
        return self.__str__()

    def short_repr(self):
        return 'ws{id}'.format(id=self.id)
