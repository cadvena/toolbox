#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "Chris Advena"
__version__ = "0.0.1"
__license__ = "MIT"

import os
from datetime import datetime as dtdt
from shutil import rmtree
import random
import string
from collections import deque
from toolbox.appdirs import site_temp_dir
from toolbox.swiss_army import datetime_to_str, datetime_filename_precise_fmt, datetime_filename_fmt

from toolbox.pathlib import Path

try:
    from logzero import logger
except:
    # from datetime import datetime as dtdt
    class Logger:
        def __init__(self, log_file = None):
            self.log_file = log_file
            if not log_file: self.log_file = os.path.basename(os.path.splitext (__file__)[0]) + \
                                             '.log'
            self.fmt = '%Y/%m/%d %H:%M:%S'

        def now_str(self):
            return dtdt.now ().strftime (self.fmt)

        def log(self, *args, level = 'I'):
            with open (self.log_file, mode = "a") as file:
                for arg in args:
                    line = '[' + level + ' ' + dtdt.now ().strftime (self.fmt) + ']  ' + str (arg)
                    file.write (line)
                    print (line)

        info = log
        warn = log
    logger = Logger()


r"""
Allowed Characters in filenames:
    Microsoft: https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file
        Use any character in the current code page for a name, including Unicode characters and 
        characters in the extended character set (128–255), except for the following:
            - The following reserved characters:
                < (less than)
                > (greater than)
                : (colon)
                " (double quote)
                / (forward slash)
                \ (backslash)
                | (vertical bar or pipe)
                ? (question mark)
                * (asterisk)
            - Integer value zero, sometimes referred to as the ASCII NUL character.
            - Characters whose integer representations are in the range from 1 through 31, except 
                for alternate data streams where these characters are allowed. For more information 
                about file streams, see File Streams.
            - Any other character that the target file system does not allow.
    Generally avoid:
        #%&{}\<>*?/ $!'":@+`|=
"""

temp_files = deque()
temp_dirs = deque()

default_temp_dir = site_temp_dir()
valid_chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ(),-.;[]^_'
# default_temp_dir = os.environ['temp']
# default_temp_dir = os.path.join (os.getcwd (), 'temp_files')

def rand_str(length: int = 12, chars = None):
    assert (length >= 0)
    if not chars: chars = valid_chars
    assert (len (chars) > 0)
    return ''.join (random.choices (chars, k = length))

class TempDir:
    def __init__(self, length=16, include_datetime=False,
              root=default_temp_dir, parents = True):
        """

        :param length:    length of file basename, like "stem.suffix"
        :param suffix:    if not provided, one will be created
        :param include_datetime:  True: datetime included in filename at end of stem, before suffix.
                                 False: datetime not included in filename
        :param root:      if specified, create temp_file in this location,
                          else create temp_file in working directory.
        :param parents:   if True, create root folder structure.
        :param as_bytes:  True: create a binary/bytes file
                           False: create a text file (default)
        """
        if os.path.exists(root):
            if not(os.path.isdir(root) or os.path.islink(root)):
                raise FileExistsError(f'root "{root}" is an existing file. {e}')

        pathname = ''
        while os.path.exists(pathname) or not pathname:
            pathname = self.generate_dir_name(length = length,
                                              include_datetime = include_datetime,
                                              root = root)
        self.path = Path(pathname, ignore_errors = False).absolute()
        self.path.mkdir(parents = parents, exist_ok = True)
        temp_dirs.append(self.path)

    @staticmethod
    def generate_dir_name(length = 16, root = None, include_datetime=False):
        result = ''
        if include_datetime:
            result += "_" + datetime_to_str(datetime_value = dtdt.now(),
                                            fmt=datetime_filename_fmt)
        result = rand_str(max(0, length - len(result))) + result
        result = result[-length:]
        if root: result = os.path.join(root, result)
        return result

    @property
    def name(self):
        return str(self.path)

    def rmtree(self):
        return rmtree(self.path, ignore_errors = True)

    def cleanup(self):
        return self.rmtree()


def temp_dir(length=16, include_datetime=False,
              root=default_temp_dir, parents = True):
    return TempDir(length = length, include_datetime = include_datetime,
                   root = root, parents = parents).path

class TempFile:
    def __init__(self, length=16, suffix='tmp', include_datetime=False,
              root=default_temp_dir, parents = True, as_bytes=False):
        """

        :param length:    length of file basename, like "stem.suffix"
        :param suffix:    if not provided, one will be created
        :param include_datetime:  True: datetime included in filename at end of stem, before suffix.
                                 False: datetime not included in filename
        :param root:      if specified, create temp_file in this location,
                          else create temp_file in working directory.
        :param parents:   if True, create root folder structure.
        :param as_bytes:  True: create a binary/bytes file
                           False: create a text file (default)
        """
        self.as_bytes = as_bytes
        if not root: raise ValueError('root cannot be empty.')
        if os.path.exists(root):
            if not(os.path.isdir(root) or os.path.islink(root)):
                raise FileExistsError(f'root "{root}" is an existing file. {e}')
        else:
            Path(root, ignore_errors = False).mkdir(parents = parents, exist_ok = True)
        fn = self._generate_filename(length=length, suffix=suffix,
                                     include_datetime=include_datetime,
                                     root = root, parents = parents,
                                     as_bytes = as_bytes)
        fn = os.path.join(root, fn)
        self.path = Path(fn).absolute()
        self.path.parent.mkdir(parents = parents, exist_ok = True)
        if as_bytes:
            self.path.write_bytes(b'')
        else:
            self.path.write_text('')
            self._f_obj = None
        # if not isinstance(self.path, Path): self.path = Path(self.path)
        temp_files.append(self.path.absolute())

    def _generate_filename(self, length=16, suffix='', include_datetime=False,
              root=None, parents = True, as_bytes=False):
        fn = None
        while fn is None:
            fn = self.rand_filename(length = length, suffix = suffix, include_datetime =
            include_datetime)
            fn = os.path.join(root, fn)
            if os.path.exists(fn): fn = None
        return Path(fn).absolute()

    # def valid_chars(invalid_chars:str = invalid_filename_chars) -> str:
    #     return remove_invalid_chars(string.printable)

    @staticmethod
    def rand_filename(length = 16, suffix = '', include_datetime = False):
        assert (length > 4)

        valid_chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ(),-.;[]^_'
        # invalid_filename_chars = "#%&{}\\<>*?/ $!'\":@+`|="

        def rand_str(length: int = 12, chars = None):
            assert (length > 0)
            if not chars: chars = valid_chars
            assert (len (chars) > 0)
            return ''.join (random.choices (chars, k = length))

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

    def open(self, mode='r', buffering=-1,encoding=None, errors=None,
             newline=None, closefd=True):
        # https://docs.python.org/3/library/functions.html#open
        if self._f_obj: self._f_obj.close()
        self._f_obj = open(str(self.path), mode=mode, buffering=-buffering,
                           encoding=encoding, errors=errors, newline=newline,
                           closefd=closefd)

    def read(self, mode='r', buffering=-1,encoding=None, errors=None, newline=None, closefd=True):
        # https://docs.python.org/3/library/functions.html#open
        p = str(self.path)

        with open(p, mode=mode, buffering=buffering, encoding=encoding, errors=errors,
                  newline=newline, closefd=closefd) as f:
            content = f.read()
        return content

    def readlines(self, mode='r', buffering=-1,encoding=None, errors=None, newline=None,
                closefd=True):
        # https://docs.python.org/3/library/functions.html#open
        p = str(self.path)

        with open(p, mode=mode, buffering=buffering, encoding=encoding, errors=errors,
                  newline=newline, closefd=closefd) as f:
            content = f.readlines()
        return content

    def write(self, content, mode='wb'):
        # https://docs.python.org/3/library/functions.html#open
        p = str(self.path)

        with open(p, mode=mode) as f:
            f.write(content)

    def writelines(self, mode='w', buffering=-1,encoding=None, errors=None, newline=None,
                closefd=True):
        # https://docs.python.org/3/library/functions.html#open
        p = str(self.path)

        with open(p, mode=mode, buffering=buffering, encoding=encoding, errors=errors,
                  newline=newline, closefd=closefd) as f:
            f.writelines(p)

    def remove(self):
        if self._f_obj: self._f_obj.close()
        return os.remove (self.path)

    def close(self):
        if self._f_obj: self._f_obj.close()
        # return self.remove()


def temp_file(length=16, suffix='', include_datetime=False,
              root=None, parents = True, as_bytes=False):
    return TempFile(length = length, suffix = suffix, include_datetime = include_datetime,
                    root = root, parents = parents, as_bytes = as_bytes)

def _TempDir_example():
    tfp = TempDir(length = 20, include_datetime = True)
    tfp.rmtree()
    print(tfp.path)

    tfp = temp_dir(length = 10)
    print(tfp)
    Path(tfp).remove()

def _TempFile_exmaple():
    print ('\n\ntemp directory: ', default_temp_dir, '\n')
    # for i in range(10, 40):
    #     print(TempFile.rand_filename(i, suffix = '~tmp', include_datetime = True))
    for i in range (10, 15):
        tfp = TempFile (length = i).path
        fn = tfp.absolute ().str
        print (fn, ' exists:', tfp.exists ())
        # in this example, we will delete/remove every other temp file now and the others later
        if i % 2: tfp.remove ()
        print ('    ', fn, ' exists:', os.path.exists (fn))

    print ('temp files deque size: ', len (temp_files))
    del_cnt = 0
    while len (temp_files) > 0:
        fn = temp_files.pop ()
        if os.path.exists (fn):
            os.remove (fn)
            del_cnt += 1
            print ('    removed: ', fn)
        else:
            print ('    not found: ', fn)
    print ('temp files deleted: ', del_cnt)
    print ('temp files deque size: ', len (temp_files))

# Do not delete main()
def main():
    """ Main entry point of the app """
    logger.info("Logging for {__name__}.main() in <{__file__}>")


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()
    # _TempDir_example()
    _TempFile_exmaple()
