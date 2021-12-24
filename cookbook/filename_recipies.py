import random
import string
from datetime import datetime as dtdt
from toolbox.swiss_army import datetime_to_str, datetime_filename_precise_fmt

invalid_filename_chars = "#%&{}\\<>*?/ $!'\":@+`|="
valid_chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ(),-.;[]^_'


def rand_str(length: int = 12, chars = None):
    """
    Create a string of random characters of specified length
    :param length: length of returned string
    :param chars: characters to select from when building string
    :return: string of characters randomly selected from chars
    """
    assert (length > 0)
    if not chars: chars = valid_chars
    assert (len (chars) > 0)
    return ''.join (random.choices (chars, k = length))


def rand_filename(length = 16, suffix = '', include_datetime = False):
    """
    Creates a random filename, essentially a random string of characters that
    are permissible in a filename.  Returns a filename like "stem.suffix", no
    drive:/folder/ component.
    :param length: length of the filename returned (including suffix)
    :param suffix: if none provided, a random 3 to 5 character suffix (4 to 6
    including the '.') is created.
    :param include_datetime: If True, a datetime value is inserted at the end of
                             the stem, before the suffix.
    :return: a randomly generated filename of specified length.
    """
    assert (length > 4)

    result = ''
    # append suffix
    if suffix and not suffix.startswith ("."):
        suffix = '.' + suffix
    elif not suffix:
        i = 3
        if length - len (result) > 7: i = 5
        suffix = '.' + rand_str (3, chars = string.ascii_lowercase)
    result += suffix

    # add datetime to filename
    if include_datetime:
        date_str = datetime_to_str (dtdt.now (), datetime_filename_precise_fmt)
        result = date_str[:max (length - len (suffix), 15)] + result

    # prepend random characters to filename
    if len (result) < length:
        result = rand_str (length - len (result), valid_chars) + result
    return result[-length:]


def str_replace(str_in, sub_str, new_sub_str):
    """
    This is an example; it is not meant to replace the built-in replace method
    of the str class.

    Within str_in, find and replace all occurrences of sub_str with new_sub_str
    :param str_in:
    :param sub_str:
    :param new_substr:
    :return:
    """
    return str_in.replace(sub_str, new_sub_str)


def remove_invalid_chars(str_in: str, invalid_chars: str = invalid_filename_chars) -> str:
    """
    remove all occurrences of each character from invalid_chars from str_in.
    example: remove_invalid_chars(r't#h|++e %q:u&i@ck{ br}o!wn\ fo\'x ju~mp?s" ov$e=r t|he `laz<y dog')
             returns: 'thequickbrownfoxjumpsoverthelazydog'
    :param str_in:
    :param invalid_chars:
    :return:
    """
    result = str_in
    for c in invalid_chars:
        result = result.replace (c, '')
    # remove unprintable characters of AsCII value 0-31
    for i in range (max (32, min ([ord (c) for c in result]))):
        result = result.replace (chr (i), '')
    # remove unprintable characters of AsCII >=126
    for i in range (126, max ([ord (c) for c in result]) + 1):
        result = result.replace (chr (i), '')
    return result