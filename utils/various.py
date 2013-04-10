#!/usr/bin/python3
#-*- coding: utf-8 -*-
# This code is PEP8-compliant. See http://www.python.org/dev/peps/pep-0008/.
"""

Wyrd In: Time tracker and task manager
CC-Share Alike 2012 © The Wyrd In team
https://github.com/WyrdIn

This module collects rather universal utility functions.

"""
from contextlib import contextmanager
import os.path
from shutil import copy2, move


@contextmanager
def open_backed_up(fname, mode='r', suffix='~'):
    """A context manager for opening a file with a backup. If an exception is
    raised during manipulating the file, the file is restored from the backup
    before the exception is reraised.

    Keyword arguments:
        - fname: path towards the file to be opened
        - mode: mode of opening the file (passed on to open()) (default: "r")
        - suffix: the suffix to use for the backup file (default: "~")

    """
    # If the file does not exist, create it.
    if not os.path.exists(fname):
        open(fname, 'w').close()
        bak_fname = None
    # If it does exist, create a backup.
    else:
        bak_fname = fname + suffix
        copy2(fname, bak_fname)
    try:
        f = open(fname, mode)
        yield f
    except Exception as e:
        if bak_fname is not None:
            move(bak_fname, fname)
        raise e
    # Closing.
    f.close()


def group_by(objects, attrs, single_attr=False):
    """Groups `objects' by the values of their attributes `attrs'.

    Returns a dictionary mapping from a tuple of attribute values to a list of
    objects with those attribute values.

    keyword arguments:
        - single_attr: specifies that there is just one attribute to use as the
                       key, and that the keys should be directly values of the
                       attribute, rather than one-tuples

    """
    # Specifying one string shall be interpreted as the single attribute name,
    # rather than a sequence of one-letter attribute names.
    if isinstance(attrs, str):
        attrs = (attrs, )
    if single_attr and len(attrs) != 1:
        raise ValueError("single_attr specified, but multiple attrs used " + \
                         "for indexing.")
    if single_attr:
        attr = attrs[0]

    groups = dict()
    for obj in objects:
        if single_attr:
            key = obj.__dict__[attr]
        else:
            key = tuple(obj.__dict__[attr] for attr in attrs)
        groups.setdefault(key, []).append(obj)
    return groups


def format_timedelta(timedelta):
    """Formats a timedelta object to a string by throwing off the microsecond
    part from the standard timedelta string representation.

    """
    whole_repr = str(timedelta) + '.'
    return whole_repr[:whole_repr.find('.')]
