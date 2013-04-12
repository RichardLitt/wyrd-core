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
from datetime import datetime, timedelta, timezone
### What is pytz doing, again?
### pytz provides timezone definitions. However, since only UTC is needed here,
### we can leave it out.
# import pytz
import re


from grouping import SoeGrouping
from worktime import Interval, dayend, daystart
import wyrdin

### What do the next three lines do?
### They define regexes for a sequence of dashes (to tell an interval), a float
### number, and a timedelta specification.
_dashes_rx = re.compile('-+')
_float_subrx = r'(?:-\s*)?(?:\d+(?:\.\d+)?|\.\d+)'
_timedelta_rx = re.compile((r'\W*?(?:({flt})\s*d(?:ays?\W+)?\W*?)?'
                            r'(?:({flt})\s*h(?:(?:ou)?rs?\W+)?\W*?)?'
                            r'(?:({flt})\s*m(?:in(?:ute)?s?\W+)?\W*?)?'
                            r'(?:({flt})\s*s(?:ec(?:ond)?s?)?\W*?)?$')\
                           .format(flt=_float_subrx),
                           re.IGNORECASE)

### So dtstr is a string? And the others are, options? What does **kwargs do
### here? What's an example, then?
### Yes, all methods here have a string as an argument, and here it is `dtstr'.
### For the other arguments, see the docstring, please. kwargs are there to
### comply with a generic signature of parser methods. We want to have the same
### signature for parser methods for we provide the `get_parser' method, and its
### caller will not know what specific signature should there be for the
### particular type.
def parse_datetime(dtstr, tz=None, exact=False, orig_val=None, **kwargs):
    """Parses a string into a datetime object.

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
    ### Meaning?
    ### Originally, I wrote just a keyword -> value mapping. So I added this
    ### comment not to forget to _actually_ implement the method.
    # TODO Crude NLP.
    exact_dt = None
    ### I don't understand - would this be matching someone saying 'the end of
    ### the world? It's quite difficult for me to parse this regex.
    ### Exactly ;) It is an example how keywords could look like.
    # Try to use some keywords.
    keywords = [(re.compile(r"^\s*(?:the\s+)?end\s+of\s+(?:the\s+)?"
                            r"world(?:\s+(?:20|')12)?$"),
                 datetime(year=2012, month=12, day=21,
                          hour=11, minute=11, tzinfo=timezone.utc))]
    dtstr = dtstr.strip()
    lower = dtstr.lower()
    for keyword, dt in keywords:
        if keyword.match(lower):
            ### So, above - exact_dt = None - does all of the NLP, but
            ### currently doesn't actually do any of it?
            ### To some extent. Now, something moderately sophisticated (regex
            ### matching) happens below in the call `parse_timedelta(dtstr)'.
            exact_dt = dt
            break

    # If keywords did not fire, try to interpret the string as a full datetime
    # specification.
    if exact_dt is None:
        try:
            exact_dt = datetime.strptime(
                dtstr, wyrdin.session.config['TIME_FORMAT_REPR'])
        except ValueError:
            pass
    if exact_dt is None:
        try:
            exact_dt = datetime.strptime(
                dtstr, wyrdin.session.config['TIME_FORMAT_USER'])
            # FIXME Check that year is not specified as part of
            # wyrdin.session.config['TIME_FORMAT_USER']
            exact_dt = exact_dt.replace(year=datetime.now().year)
        except ValueError:
            pass

    # TODO Match regexes such as "(.*) ago", "before (.*)", "in (.*)", "after
    # (.*)" etc.

    # Try interpret the string as a timedelta and add to datetime.now().
    if exact_dt is None:
        if tz is None:
            tz = wyrdin.session.config['TIMEZONE']
        try:
            exact_dt = datetime.now(tz) + parse_timedelta(dtstr)
        except ValueError:
            raise ValueError('Could not parse datetime from "{arg}".'\
                             .format(arg=dtstr))

    # Try to supply the timezone from the original value.
    if exact_dt.tzinfo is None:
        if tz is not None:
            exact_dt = exact_dt.replace(tzinfo=tz)
        elif (orig_val is not None and orig_val.tzinfo is not None):
            exact_dt = exact_dt.replace(tzinfo=orig_val.tzinfo)

    # Round out microseconds (that's part of NLP) unless asked to return the
    # exact datetime.
    return exact_dt if exact else exact_dt.replace(microsecond=0)

### What's the difference between a timedelta and a datetime object? Do we need
### both?
### Sure we do. `timedelta' is time difference, `datetime' is a time point
### specified by its date and time. Please, look in the documentation.
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

### Shouldn't the be packages for this? I don't know what Interval or Grouping
### are. :/
### There is one. wyrdin. Look for "modules" in Python documentation, read the
### imports close to the beginning of this file again. Interval and Grouping
### are then documented in their defining modules.
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
    ivalstr_l = ivalstr.strip().lower()
    if ivalstr_l in keywords:
        start, end = keywords[ivalstr_l]
        return Interval(start, end)

    # Match some more patterns.
    if ivalstr_l.startswith('since'):
        start_str = ivalstr[5:].strip()
        return Interval(parse_datetime(start_str, tz=tz, exact=exact), now)

    # Parse the interval in the form A--B.
    start, end = _dashes_rx.split(ivalstr, 2)
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
