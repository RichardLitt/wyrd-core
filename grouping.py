#!/usr/bin/python3
#-*- coding: utf-8 -*-
# This code is PEP8-compliant. See http://www.python.org/dev/peps/pep-0008/.
"""

Wyrd In: Time tracker and task manager
CC-Share Alike 2012 © The Wyrd In team
https://github.com/WyrdIn

This module implements boolean groupings of things -- nested conjunctions and
disjunctions.

"""

import re

from backend.generic import DBObject


class SoeGrouping(DBObject):
    """A structured grouping of SOEs -- states or events."""
    _id_from_str_rx = re.compile(r'^.*?(\d+)\s*$')  # select the last chunk of
                                                    # digits

    def __init__(self, elems=None, id=None, short_repr=None):
        """Creates a SOE grouping.

        Keyword arguments:
            - elems: elements of this grouping; may be None, may be a list of
                     StateOrEvents or SoeGroupings (a mixed list of both)
            - id: an ID (a number) of the object, if a specific one is
                  required; if ID is supplied, it has to be non-negative
                  integer larger than any of IDs for this type of object
                  assigned so far
            - short_repr: the return value of short_repr() called on an object
                          of this class before serialisation

        """
        if short_repr is not None:
            id = int(self._id_from_str_rx.sub(r'\1', short_repr))
        super(SoeGrouping, self).__init__(id)
        if elems is not None:
            self.elems = elems
        else:
            self.elems = list()

    @property
    def done(self):
        raise NotImplementedError("The abstract SoeGrouping does not specify "
                                  "when it is done.")

    def short_repr(self):
        return 'g{id}'.format(id=self.id)


class AndGroup(SoeGrouping):
    """A conjunctive group of SOEs -- all of them need to be current in order
    for the group to be current.

    """
    name = "and"

    @property
    def done(self):
        return all(map(lambda elem: elem.done, self.elems))

    def short_repr(self):
        return 'ga{id}'.format(id=self.id)


class OrGroup(SoeGrouping):
    """A disjunctive group of SOEs -- any of them need to be current in order
    for the group to be current.

    """
    name = "or"

    @property
    def done(self):
        return any(map(lambda elem: elem.done, self.elems))

    def short_repr(self):
        return 'go{id}'.format(id=self.id)


class ListGroup(AndGroup):
    """A list of SOEs -- they should happen in a given order. When the last one
    is done, the group is fulfilled (same as AndGroup).

    """
    name = "list"

    def short_repr(self):
        return 'gl{id}'.format(id=self.id)
