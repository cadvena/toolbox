from collections.abc import Iterable
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime as dtdt
from datetime import timedelta, date, tzinfo
import time as _time
import pytz
import re
import dateutil  #parser, tz
from calendar import monthrange
from collections import namedtuple
# from inspect import ismodule
from types import GeneratorType
from typing import Union
from urllib.parse import urlparse as _urlparse
from collections import namedtuple

# ##############################################################################
# Constants and Variables
# ##############################################################################
ModuleType = type(sys)
NoneType = type(None)
_trues = (True, 'true', 'yes', 1)
_falses = (False, 'false', 'no', 0, None)
py_ver = float(f'{sys.version_info.major}.{str(sys.version_info.minor).rjust(2, "0")[-2:]}'
               f'{str(sys.version_info.micro).rjust(2, "0")[-2:]}')
ZERO = timedelta(0)
HOUR = timedelta(hours=1)
SECOND = timedelta(seconds=1)
UTCOFFSET = dtdt.utcnow() - dtdt.now()
STDOFFSET = timedelta(seconds = -_time.timezone)
if _time.daylight:
    DSTOFFSET = timedelta(seconds = -_time.altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET

# ##############################################################################
# Handy tools
# ##############################################################################

# datetime tools
# ##############################################################################
# datetime cheatsheet: https://strftime.org/
tz_suffix = ' %Z%z'
datetime_us_fmt = '%m/%d/%Y %H:%M:%S'
datetime_us_precise_fmt = '%m/%d/%Y %H:%M:%S.%f'
date_us_fmt = '%m/%d/%Y'
time_us_fmt = '%H:%M:%S'
time_us_precise_fmt = '%H:%M:%S.%f'
date_filename_fmt = '%Y%m%d'
datetime_filename_fmt = '%Y%m%d_%H%M%S'
datetime_filename_precise_fmt = '%Y%m%d_%H%M%S%f'
# us_timezones = tuple([s for s in pytz.common_timezones if s.startswith('US')])

class LocalTimezone(tzinfo):
    def fromutc(self, dt):
        assert dt.tzinfo is self
        stamp = (dt - dtdt(1970, 1, 1, tzinfo=self)) // SECOND
        args = _time.localtime(stamp)[:6]
        dst_diff = DSTDIFF // SECOND
        # Detect fold
        fold = (args == _time.localtime(stamp - dst_diff))
        return dtdt(*args, microsecond=dt.microsecond,
                        tzinfo=self, fold=fold)

    def utcoffset(self, dt):
        if self._isdst(dt):
            return DSTOFFSET
        else:
            return STDOFFSET

    def dst(self, dt):
        if self._isdst(dt):
            return DSTDIFF
        else:
            return ZERO

    def tzname(self, dt):
        return _time.tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, 0)
        stamp = _time.mktime(tt)
        tt = _time.localtime(stamp)
        return tt.tm_isdst > 0

def find_tz(tz_substr: str, as_tz: bool = False):
    """
    find a timezone by name
    :param tz_substr: full or partial name of a timezone
    :param as_tz: False (default): return a tuple of timezone names
                  True: return a tuple of tzinfo object
    :return: tuple of timezone names or tzinfo objects
    """
    result =  [tz_name for tz_name in pytz.common_timezones
                  if tz_substr.lower() in tz_name.lower()]
    if as_tz:
        result = [pytz.timezone(s) for s in result]

    return tuple(result)


def add_months(datetime_value: Union[dtdt, date], months: int):
    """
    Add one month to either a date or datetime value.
    :param datetime_value: a datetime.date or datetime.datetime value
    :param months: number of months to add (negative number to subtract)
    :return: date or datetime value equal to datetime_val + months
    """
    # from calendar import monthrange
    if months == 0 : return datetime_value
    month = datetime_value.month - 1 + months
    year = datetime_value.year + month // 12
    month = month % 12 + 1
    day = min(datetime_value.day, monthrange(year, month)[1])
    if type(datetime_value) == date:
        return date(year, month, day)
    else:
        hour = datetime_value.hour
        minute = datetime_value.minute
        sec = datetime_value.second
        frac = datetime_value.microsecond
        return dtdt(year, month, day, hour, minute, sec, frac)


def datetime_add(datetime_value:dtdt = dtdt.now(), years:int = 0, months:int = 0,
                 weeks:int =0, days:int =0, hours:int =0, minutes:int =0,
                 seconds:int =0, **kwargs):
    """
    Adds specified increments of time to datetime_value.
    :param datetime_value: the datetime.datetime to increment (or decrement)
    :param years: years
    :param months: months
    :param weeks: weeks
    :param days: days
    :param hours: hours
    :param minutes: minutes
    :param seconds: seconds
    :param kwargs: see https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Timedelta.html#
                    Available kwargs: {days, seconds, microseconds, milliseconds, minutes, hours,
                    weeks}. Values for construction in compat with datetime.timedelta. Numpy ints
                    and floats will be coerced to python ints and floats.
    :return: datetime.datetime
    """
    d = datetime_value
    if years !=0: d = dtdt(d.year + years, d.month, d.day, d.hour, d.minute, d.second,
                           d.microsecond)
    if months !=0: d = add_months(d, months)
    return d + timedelta(days=days, weeks=weeks, hours=hours, minutes=minutes,
                         seconds=seconds, **kwargs)


def datetime_to_str(datetime_value: dtdt = None, fmt = datetime_us_fmt) -> str:
    if not datetime_value: datetime_value = dtdt.now()
    return datetime_value.strftime(fmt)


def str_to_datetime(date_str:str, fmt: str = datetime_us_precise_fmt) -> dtdt:
    try:
        return dtdt.strptime(date_str, fmt)
    except:
        if fmt in [datetime_us_precise_fmt, datetime_us_fmt, date_us_fmt]:
            fmt = datetime_us_precise_fmt[:len(date_str)-2]
        try:
            return dtdt.strptime(date_str, fmt)
        except:
            raise


def str_to_time(time_str:str, fmt: str = time_us_precise_fmt) -> dtdt:
    try:
        return dtdt.strptime(time_str, fmt)
    except:
        if fmt in [time_us_precise_fmt, time_us_fmt]:
            fmt = datetime_us_precise_fmt[:len(time_str)]
        try:
            return dtdt.strptime(time_str, fmt)
        except:
            raise


def utc2ept(utc_time: dtdt = dtdt.now()):
    t1 = utc_time.astimezone(pytz.utc)  # .replace(tzinfo = None)
    t2 = utc_time.replace(tzinfo = pytz.utc)  # .replace(tzinfo = None)
    if utc_time.tzinfo and t1 != t2:
        raise ValueError(f'tzinfo must be UTC or None, not {utc_time.tzinfo}.')
    return utc_time.replace(tzinfo=pytz.utc)


def ept2utc(ept_time: dtdt = dtdt.now()):
    t1 = ept_time.astimezone(pytz.timezone('US/Eastern')).replace(tzinfo = None)
    t2 = ept_time.replace(tzinfo = pytz.timezone('US/Eastern')).replace(tzinfo = None)
    if ept_time.tzinfo and t1 != t2:
        raise ValueError(f'tzinfo must be US/Eastern or None, not {ept_time.tzinfo}.')
    return ept_time.replace(tzinfo=pytz.timezone('US/Eastern'))


def local2utc(local_datetime: dtdt = dtdt.now()):
    t1 = local_datetime.replace(tzinfo = None)
    t2 = local_datetime.astimezone().replace(tzinfo = None)
    if local_datetime.tzinfo and t1 != t2:
        raise ValueError(f'tzinfo must be the current local zone or None, not {local_datetime.tzinfo}.')
    return local_datetime.astimezone()


def utc2local(utc_datetime: dtdt):
    t1 = utc_datetime.astimezone(pytz.utc)  # .replace(tzinfo = None)
    t2 = utc_datetime.replace(tzinfo = pytz.utc)  # .replace(tzinfo = None)
    if utc_datetime.tzinfo and t1 != t2:
        raise ValueError(f'tzinfo must be UTC or None, not {utc_datetime.tzinfo}.')

    # assert utc_datetime.tzinfo is dtdt.tzinfo
    stamp = (utc_datetime - dtdt(1970, 1, 1)) // SECOND
    args = _time.localtime (stamp)[:6]
    dst_diff = DSTDIFF // SECOND
    # Detect fold
    fold = (args == _time.localtime (stamp - dst_diff))
    return dtdt(*args, microsecond = utc_datetime.microsecond, fold = fold)




    # now_timestamp = time.time()
    # offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    # return utc_datetime + offset
# ##############################################################################
# Iterable
# ##############################################################################
def itertuple(tuple_in: namedtuple):
    for i, f in enumerate (tuple_in._fields):
        yield f, tuple_in[i]
    return


def namedtuple2dict(tuple_in: namedtuple) -> dict:
    return dict(itertuple(tuple_in))


def is_iterable(anything):
    if isinstance(anything, Iterable) \
    or hasattr (anything, '__iter__'):
        return True
    else:
        return False


def make_iterable(anything, return_type = list,
                  string_is_iterable: bool = True,
                  *split_args, **split_kwargs):
    """
    In some cases, you want to create a function or method that accepts an
    argument that is an iterable but want the caller of the function to be able
    to provide a non-iterable.  This function attempts to facilitate the
    conversion of a non-iterable to an iterable, so this code does not have
    to repeated in many places.
    :param anything: a python object.  At this time, functions and classes are
                     not supported (with a couple exceptions)
    :param string_is_iterable: True: do NOT convert string to return_type
                              False: DO convert string to return_type
    :param return_type: a type that is iterable, such as list, tuple, or set
                        OR a supported class from: pandas DataFrame, Numpy array
    :return: an iterable
    """
    if return_type == dict:
        raise NotImplementedError('return_type "dict" not supported. make_iterable error 01')
    elif type(anything) == type(None):
        try:
            return return_type()
        except:
            raise NotImplementedError('return_type "dict" not supported. make_iterable error 02')
    elif isinstance(return_type, pd.DataFrame):
        return pd.DataFrame(anything)
    # elif isinstance(return_type, type(np.array([]))) \
    # or isinstance(return_type, np.array):
    elif isinstance(return_type, type(np.array([]))):
        return np.array(anything)
    elif type(anything) == str:
        if string_is_iterable:
            return anything
        else:
            result = [s.strip(', ') for s in anything.split()]
            try:
                return return_type(result)
            except TypeError:
                msg = 'In make_iterable() return_type of  "{return_type}" ' + \
                      'is not implemented. make_iterable error 03'
                raise NotImplementedError(msg)
                # return result
    elif is_iterable (anything):
        return anything
    elif type(anything) in [int, float, bool]:
        return [anything]
    elif callable(anything):
        # anything is a function
        msg = 'return_type that is callable (e.g., function or class) ' + \
              'not supported. make_iterable error 04'
        raise NotImplementedError(msg)
    else:
        try:
            return return_type(anything)
        except:
            msg = 'In make_iterable() return_type of  "{return_type}" ' + \
                  'is not implemented. make_iterable error 05'
            raise NotImplementedError (msg)
            # return result

# data type tools
# ##############################################################################


def boolify(value_in,
            trues = _trues,
            falses = _falses):
    """
    Attempt to convert value_in (of any type) to a boolean, where value_in
    is a boolean, number, str or any value in trues or falses. String
    comparison is case-insensitive.
    :param value_in: the value to be converted to a boolean.
    :param trues: list-like of values to be interpreted as True
    :param falses: list-like of values to be interpreted as False
    :return:
    """
    # If python can natively recognize value_in as bool, then we need go no further.
    if type(value_in) == bool:
        return value_in
    elif value_in == True:
        # this should never be reached?
        return True
    elif value_in == False:
        # this should never be reached?
        return False

    # if value_in is a string, see if that string is in trues or falses (case
    # insensitive comparison).
    if type(value_in) == str:
        # value_in IS a string.  Let's see if value_in matches a string from
        # trues or falses.

        # Prep value_in, trues, and falses so that:
        # 1) strip leading/lagging whitespace from value_in.
        # 2) since value_in is a string, get rid of non-strings from trues and
        #    falses; we don't need to compare to non-strings. And, convert the
        #    remaining values in trues and falses to lowercase for case
        #    insensitive comparison.
        if len(value_in.strip()) > 0: value_in = value_in.strip()
        trues = [s.lower() for s in trues if type(s) == str]
        falses = [s.lower() for s in falses if type(s) == str]

        if value_in.lower() in trues:
            return True
        elif value_in.lower() in falses:
            return False
        else:
            # value_in is a str but is NOT any value from trues or falses, so
            # we cannot convert it to True or False.
            raise ValueError(f'"{value_in}" cannot be converted to a boolean')
    elif value_in in trues:
        # value_in is not a string but is in trues
        return True
    elif value_in in falses:
        # value_in is not a string but is in falses
        return False
    else:
        # value_in is not a native bool and cannot be found in trues or falses.
        raise ValueError (f'"{value_in}" cannot be converted to a boolean')


def auto_type_str(str_in: str,
                  trues = _trues,
                  falses = _falses):
    """
    Attempt to automatically convert value_in to an obvious type, such as
    converting '123' to 123.  Optionally, you can set recurse = True to
    recursively inspect and convert the items in a recursive object (like a list
    or dict).

    :param str_in: the value to be re-typed to int, float or bool
    :param trues:
    :param falses:
    :return:
    """
    assert(type(str_in) in [NoneType, str])
    if not str_in:
        return str_in

    str_in = str_in.strip()

    # def str_to_num(str_in):
    # https://stackoverflow.com/questions/44891070/whats-the-difference-between-str-isdigit-isnumeric-and-isdecimal-in-python
    if str_in.isdecimal():
        return int(str_in)
    elif str_in.isalpha():
        return str_in
    elif str_in.isdecimal():
        return int(str_in)
        # raise NotImplementedError
    elif str_in.isnumeric():
        # '½'.isnumeric() returns True
        return str_in
        # raise NotImplementedError
    elif str_in.isdigit():
        # '³'.isdigit() ruturns True
        return str_in
        # raise NotImplementedError
    elif str_in.count('.') == 1 \
            and not str_in.startswith('.') \
            and all([s in '0123456789.' for s in str_in]):
        if str_in.endswith('.'): str_in += '0'
        return float(str)

    trues = [s.lower() for s in trues]
    falses = [s.lower() for s in falses]
    if str_in.lower() in trues:
        return True
    elif str_in.lower() in trues:
        return False
    else:
        return str_in


def auto_type(value_in, recurse:bool = True):
    """
    Attempt to automatically convert value_in to an obvious type, such as
    converting '123' to 123.  Optionally, you can set recurse = True to
    recursively inspect and convert the items in a recursive object (like a list
    or dict).
    :param value_in: the value to be re-typed
    :param recurse:  True: recursively inspect and convert the items in a
                           recursive object (like a list or dict).
                    False: items in iterables are not inspected and converted.
    :return: the value of value_in, possibly converted to another data type.
    """
    t = type(value_in)
    if is_iterable(anything = value_in):
        if not recurse:
            return value_in
        elif t in [tuple, list]:
            result = [auto_type(x, recurse) for x in value_in]
            if t == tuple:
                result = tuple(result)
            return result
        elif t == dict:
            result = {}
            for k, v in value_in.items:
                result.append(auto_type(k, recurse), auto_type(v, recurse))
            return result
        elif t == pd.DataFrame or isinstance(value_in, np.ndarray) \
                               or isinstance(value_in, GeneratorType):
            return value_in
        else:
            raise NotImplementedError
    if type(value_in) == str:
        return auto_type_str(str_in = value_in)
    elif type(value_in) == float:
        if value_in == int(value_in):
            return int(value_in)

# ##############################################################################
# Misc
# ##############################################################################

def insert_datestr_in_filename(s: str, fmt = datetime_filename_fmt):
    s, ext = os.path.splitext(s)
    return s + '_' + dtdt.now ().strftime(fmt) + ext

def flowerbox(title: str, length:int = 80, double:bool =False, symbol="#"):
    line = '\n'+symbol*length
    if double: line += line
    print(line)
    if double: print(symbol*2)
    print(f'\n{symbol} {title}\n' )
    if double: print(symbol*2)
    print(line)
# misc tools


def parse_version_info(version) -> list:
    if isinstance(version, (list, tuple)):
        result = list(version)
    elif type(version) in (int, float, str):
        result = str(version)
        result = result.split ('.')
    else:
        raise TypeError(f'version must be one of these types: list, tuple, str, int, float.')

    # try to convert each part of the version from string to number
    for i, s in enumerate(result):
        if type(s) == str:
            if s.isnumeric():
                result[i] = int(s)
            elif s.isdecimal():
                result[i] = float(s)

    if len(result) == 0:
        # major version number
        result.append(0)
        # result.append(int(dtdt.now().date().strftime("%Y")))
    if len(result) == 1:
        # minor version
        result.append(0)
        # result.append(int(dtdt.now ().date ().strftime ("%m")))
    if len(result) == 2:
        # micro = 0
        result.append(0)
    VersionTuple = namedtuple ('VersionTuple', ['major', 'minor', 'micro'])
    return VersionTuple(result[0], result[1], result[2])


def version_info(package: ModuleType):
    """
    many modules have both .__version__ and .__version_info__
    information
    :param package:
    :return:
    """
    assert(type(package) == ModuleType)
    if hasattr(package, "__version_info__"):
        return parse_version_info(package.__version_info__)
    elif hasattr(package, "__version__"):
        return parse_version_info(package.__version__)
    else:
        raise AttributeError(f'Module {package.__name__} does not contain version information.')


def urlparse(url) -> tuple:
    ParseResult = namedtuple('ParseResult', ['scheme', 'netloc', 'path', 'params',
                                              'query', 'fragment', 'username',
                                              'password', 'hostname', 'port'])
    parts = _urlparse(url)
    if "//" in url:
        return ParseResult(parts.scheme, parts.netloc, parts.path,
                            parts.params, parts.query, parts.fragment, parts.username,
                            parts.password, parts.hostname, parts.port)
    # elif re.search(r'\..*/.+', url):
    elif '/' in url:
        subparts = parts.path.split('/')
        return ParseResult(parts.scheme, subparts[0], parts.path[len(subparts[0]):],
                           parts.params, parts.query, parts.fragment, parts.username,
                           parts.password, subparts[0], parts.port)
    elif '.' in url:
        return ParseResult(parts.scheme, parts.path, '', parts.params, parts.query, parts.fragment, parts.username,
                           parts.password, parts.path, parts.port)
    else:
        return ParseResult(parts.scheme, parts.path, '', parts.params, parts.query, parts.fragment, parts.username,
                           parts.password, parts.path, parts.port)


def is_valid_url(url: str):
    url=url.lower()
    # Regex to check valid URL
    regex = ("((http|https|ftp|ftps)://)([a-zA-Z0-9])+" +
             "([a-zA-Z0-9]+.)?[a-zA-Z0-9@:%._\\+~#?&//=]" +
             "{2,256}\\.[a-z]" +
             "{2,6}\\b([-a-zA-Z0-9@:%" +
             "._\\+~#?&//=]*)")

    # Compile the ReGex
    p = re.compile(regex)

    # If the string is empty
    # return false
    if (url == None):
        return False

    # Return if the string
    # matched the ReGex
    if (re.search(p, url)):
        return True
    else:
        return False


# ##############################################################################
# Examples
# ##############################################################################


def _example_urlparse():
    for url in ['https://www.youtube.com/watch?v=YR12Z8f1Dh8&feature=relmfu',
                'youtube.com/watch?v=YR12Z8f1Dh8&feature=relmfu',
                'pjm.com/folder1/folder2/index.html',
                'pjm.com/oasis/index.html',
                'www.pjm.com',
                'pjm.com',
                'www.',
                'www',
                ]:
        print ('2. URL:', url, '\n   ', urlparse (url))


def _examples():
    res = make_iterable('comma, separated, string', string_is_iterable = False, sep=",")
    print(res)
    print ('\n\n')

    test_make_iterable = True
    if test_make_iterable:
        things = (is_iterable, pd, 0.0, 0, 'a, b, c, d', None, '')
        return_types = (list, tuple, set, pd.DataFrame, np.array, is_iterable,
                        'space separated string',  'comma, separated, string')
        for thing in things:
            indent = 0
            print (' ' * indent, '=' * (60-indent))
            print(type(thing).__name__, thing)
            print (' ' * indent, '=' * (60-indent))
            if type(thing) == str:
                bools = [True, False]
            else:
                bools = [True]
            for b in bools:
                indent = 4
                if type (thing) == str:
                    print (' ' * indent, '=' * (60-indent))
                    print (' '*indent, b)
                    indent = 8
                for rt in return_types:
                    # print('\n')
                    print (' ' * indent, '-' * (60-indent))
                    print(' '*indent, '-'*(60-indent))
                    rt_name = str(rt)
                    if hasattr(rt, '__name__'): rt_name = rt.__name__
                    # print( f'From {type(thing).__name__} "{thing}", return {rt_name}')
                    print(' '*indent, f"make_iterable(anything = {thing}, " +
                          f"string_is_iterable = {b}, return_type = {rt_name})")
                    try:
                        res = make_iterable(anything = thing,
                                            string_is_iterable = b,
                                            return_type = rt)
                        print(' '*indent, 'result: ', res)
                    except NotImplementedError:
                        print(' '*indent, 'Cannot return {rt_name} from {type(thing).__name__}')

# ##############################################################################
# Tests
# ##############################################################################

def _test_tz_converion():
    print (local2utc (dtdt.now ()))
    print ('Eastern', local2utc (dtdt.now ().astimezone (pytz.timezone ('US/Eastern'))))
    print ('NY', local2utc (dtdt.now ().astimezone (pytz.timezone ('America/New_York'))))
    try:
        x = local2utc(dtdt.now().astimezone(pytz.utc))
        if x: raise Exception('Should have raised an error')
    except ValueError as e:
        pass

    print (utc2ept (dtdt.now ()))
    print (utc2ept (dtdt.now ().astimezone (pytz.utc)))
    try:
        x = utc2ept(dtdt.now().astimezone(pytz.timezone('US/Eastern')))
        if x: raise Exception('Should have raised an error')
    except ValueError as e:
        pass

    print (ept2utc (dtdt.now ()))
    print ('Eastern', ept2utc (dtdt.now ().astimezone (pytz.timezone ('US/Eastern'))))
    print ('NY', ept2utc (dtdt.now ().astimezone (pytz.timezone ('America/New_York'))))
    try:
        x= ept2utc(dtdt.now().astimezone(pytz.utc))
        if x: raise Exception('Should have raised an error')
    except ValueError as e:
        pass



if __name__ == '__main__':
    _examples()
    _example_urlparse()
    # _test_tz_converion()


