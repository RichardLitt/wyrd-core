#!/usr/bin/python3
#-*- coding: utf-8 -*-
# This code is PEP8-compliant. See http://www.python.org/dev/peps/pep-0008/.
"""

Wyrd In: Time tracker and task manager
CC-Share Alike 2012 © The Wyrd In team
https://github.com/WyrdIn

This module implements parsers for entities used in the program. A parser is
understood as a mapping from strings to Python objects.

"""
from datetime import datetime, timedelta
import pytz
import re

from worktime import Interval, dayend, daystart
from grouping import SoeGrouping


_dashes_rx = re.compile('-+')
_float_subrx = r'(?:-\s*)?(?:\d+(?:\.\d+)?|\.\d+)'
_timedelta_rx = re.compile((r'\W*?(?:({flt})\s*d(?:ays?\W+)?\W*?)?'
                            r'(?:({flt})\s*h(?:(?:ou)?rs?\W+)?\W*?)?'
                            r'(?:({flt})\s*m(?:in(?:ute)?s?\W+)?\W*?)?'
                            r'(?:({flt})\s*s(?:ec(?:ond)?s?)?\W*?)?$')\
                           .format(flt=_float_subrx),
                           re.IGNORECASE)


def parse_datetime(dtstr, tz=None, exact=False, orig_val=None, **kwargs):
    """ Parses a string into a datetime object.

    Currently merely interprets the string as a timedelta, and adds it to now.

    Keyword arguments:
        - dtstr: the string describing the datetime
        - tz: a timezone object to consider for parsing the datetime
              (currently, the datetime specified is assumed to be in the local
              time; the timezone cannot be specified as part of the string)
        - exact: whether an exact datetime should be returned, or whether
                 microseconds should be ignored
        - orig_val: timezone will be copied from here if none was specified
                    else

    """
    # TODO Crude NLP.
    exact_dt = None
    # Try to use some keywords.
    keywords = [(re.compile(r"^\s*(?:the\s+)?end\s+of\s+(?:the\s+)?"
                            r"world(?:\s+(?:20|')12)?$"),
                 datetime(year=2012, month=12, day=21,
                          hour=11, minute=11, tzinfo=pytz.utc))]
    lower = dtstr.lower().strip()
    for keyword, dt in keywords:
        if keyword.match(lower):
            exact_dt = dt
            break

    # If keywords did not fire, interpret the string as a timedelta and add to
    # datetime.now().
    if exact_dt is None:
        if tz is None:
            tz = session.config['TIMEZONE']
        try:
            exact_dt = datetime.now(tz) + parse_timedelta(dtstr)
        except ValueError:
            raise ValueError('Could not parse datetime from "{arg}".'\
                             .format(arg=dtstr))

    # Try to supply the timezone from the original value.
    if (exact_dt.tzinfo is None and orig_val is not None
            and orig_val.tzinfo is not None):
        exact_dt = exact_dt.replace(tzinfo=orig_val.tzinfo)
    # Round out microseconds (that's part of NLP) unless asked to return the
    # exact datetime.
    return exact_dt if exact else exact_dt.replace(microsecond=0)


def parse_timedelta(timestr, **kwargs):
    """ Parses a string into a timedelta object.

    """
    rx_match = _timedelta_rx.match(timestr)
    # If the string seems to comply to the format assumed by the regex,
    if rx_match is not None:
        vals = []
        any_matched = False
        # Convert matched groups for numbers into floats one by one.
        for grp_str in rx_match.groups():
            if grp_str:
                any_matched = True
                try:
                    val = float(grp_str)
                except ValueError:
                    raise ValueError('Could not parse float from {grp}.'\
                                     .format(grp=grp_str))
            else:
                val = 0
            vals.append(val)
        # If at least one of the groups was present,
        # (In the regex, all time specifications (days, hours etc.) are
        # optional. We have to check here that at least one was supplied.)
        if any_matched:
            return timedelta(days=vals[0], hours=vals[1],
                             minutes=vals[2], seconds=vals[3])
        else:
            rx_match = None
    # If regex did not solve the problem,
    if rx_match is None:
        # Try to interpret the input as a float amount of minutes.
        try:
            return timedelta(minutes=float(timestr))
        except ValueError:
            raise ValueError('Could not parse duration from "{arg}".'\
                             .format(arg=timestr))


def parse_interval(ivalstr, tz=None, exact=False, **kwargs):
    """ Parses a string into an Interval object.

    Keyword arguments:
        - ivalstr: the string specifying the interval
        - tz: a timezone object to consider for parsing the interval
              (currently, the interval specified is assumed to be in the local
              time; the timezone cannot be specified as part of the string)
        - exact: whether the border datetimes for the interval should be
                 interpreted exactly, or whether microseconds should be ignored

    """
    now = datetime.now(tz)
    # Try to use some keywords.
    keywords = {'today': (daystart(now, tz), dayend(now, tz))}
    ivalstr = ivalstr.strip()
    if ivalstr.lower() in keywords:
        start, end = keywords[ivalstr.lower()]
        return Interval(start, end)

    # Parse the interval in the form A--B.
    start, end = _dashes_rx.split(ivalstr.strip(), 2)
    start = parse_datetime(start, tz=tz, exact=exact) if start else None
    end = parse_datetime(end, tz=tz, exact=exact) if end else None
    return Interval(start, end)


def parse_grouping(grpstr, **kwargs):
    """Parses a string into a Grouping object."""
    # Tokenise.
    tokens = list()
    # TODO Continue here.
    raise NotImplementedError('Implement parse_grouping.')
    len(tokens)


_type2parser = {datetime: parse_datetime,
                timedelta: parse_timedelta,
                SoeGrouping: parse_grouping}


def default_parser(type_):
    """Provides a default parser, especially for built-in types -- throws away
    all arguments from a parser call but the first one.

    """
    def type_parser(instr, *args, **kwargs):
        return type_(instr)
    return type_parser


def get_parser(type_):
    """Returns a parser for the given type. Parsers convert strings into
    objects of that type.

    """
    # Try to find a defined parser for the type. In case none is defined,
    # return the type itself, as in int("8").
    return _type2parser.get(type_, default_parser(type_))
