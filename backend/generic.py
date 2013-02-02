#!/usr/bin/python3
#-*- coding: utf-8 -*-
# This code is PEP8-compliant. See http://www.python.org/dev/peps/pep-0008/.
"""

Wyrd In: Time tracker and task manager
CC-Share Alike 2012 © The Wyrd In team
https://github.com/WyrdIn

"""


class DBObject(object):
    _next_id = 0

    def __init__(self, id=None):
        """Creates a new database-enabled object.

        Keyword arguments:
            - id: an ID (a number) of the object, if a specific one is
                  required; if ID is supplied, it has to be non-negative
                  integer larger than any of IDs for this type of object
                  assigned so far

        """
        cls = type(self)  # the actual (most specific) class of self
        if id is not None and id >= cls._next_id:
            self._id = id
        else:
            self._id = cls._next_id
        cls._next_id = self._id + 1

    @property
    def id(self):
        return self._id

    def short_repr(self):
        """Returns a short string which identifies the object and its type
        within the set of objects created in this WyrdIn application.

        """
        raise NotImplementedError(('{cls} does not implement the '
                                  "required method `short_repr'.").format(
                                      cls=type(self).__name__))
