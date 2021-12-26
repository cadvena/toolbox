#!/usr/bin/env python

import ftplib
import os
import tempfile
from collections import namedtuple
from typing import Union
from datetime import datetime as dtdt
from urllib.parse import urlsplit

from dateutil import parser

from toolbox import pathlib
from toolbox.file_util.hash import hash_match
# from toolbox import tb_cfg

NoneType = type(None)

# create a named tuple for results
StatsTuple = namedtuple(typename='StatsTuple',
                        field_names=('scheme', 'netloc', 'path', 'dirname',
                                     'basename', 'modified', 'size')
                        )
FTPPathParts = namedtuple('FTPPathParts', ['scheme', 'netloc', 'path',
                                           'dirname', 'basename', 'url'])
GetTuple = namedtuple(typename='GetTuple',
                      field_names=('scheme', 'netloc', 'path', 'dirname',
                                   'basename', 'modified', 'size',
                                   'target_filename')
                      )
CompareTuple = namedtuple(typename='CompareTuple',
                          field_names=['match', 'base_match', 'size_match',
                                       'modified_match', 'hash_match']
                          )


def url_join(scheme, netloc, path='') -> str:
    scheme = scheme.strip() or 'ftp'
    assert (scheme.lower() in ['ftp', 'ftps'])
    netloc = netloc.strip().strip('/')
    assert (len(netloc) > 0)
    path = path.strip().lstrip('/')
    if path: path = '/' + path
    return scheme + '://' + netloc + path


def url_split(host_or_url, source_address: tuple = None) -> FTPPathParts:
    """
    inspects host_or url to see what parts of a full url it contains,
    where a full url is like:
        scheme://netloc[/path]
        where path can be further broken down to folder/basename
        and netloc / host are interchangeable
    Example:
        ftp://ftp.pjm.com/oasis/ATCID.pdf parses to:
        scheme = 'ftp'
        netloc = 'ftp.pjm.com'
        path = '/oasis/ATCID.pdf'
                folders = '/oasis'
                basename = 'ATCID.pdf'

    :param host_or_url: can be either a host (e.g., 'ftp.pjm.com'), a
                        full url (e.g., 'ftp://ftp.pjm.com/oasis/ATCID.pdf'),
                        or any part of a full url.
    :param source_address: option 2-tuple of: host, port
    :returns:  FTPPathParts
    """
    # (scheme='ftp', netloc='ftp.pjm.com', path='/oasis/CBMID.pdf', query='', fragment='')
    scheme, host, path, query, fragment = urlsplit(host_or_url)
    if not host:
        s = path.split('/')
        if s[0].count('.') >= 2 or (len(s) > 1 and s[0].count('.') >= 1):
            host = s[0]
            path = path[len(host):]

    if '.' not in path:
        _dirname, _basename = path, ''
    else:
        _dirname, _basename = os.path.split(path)
    _dirname = _dirname.rstrip('/')
    if source_address:
        host = source_address[0] or host
    scheme = scheme or 'ftp'
    if not host:
        url = ''
    else:
        url = url_join(scheme, host, path)

    return FTPPathParts(scheme, host, path, _dirname, _basename, url)


# ##############################################################################
# API - Class
# ##############################################################################

class FTP(ftplib.FTP):
    """
    Extension of ftplib.FTP class.  See https://docs.python.org/3/library/ftplib.html.

    Return a new instance of the FTP class. When host is given, the method
    call connect(host) is made. When user is given, additionally the method
    call login(user, passwd, acct) is made (where passwd and acct default to
    the empty string when not given).

    Examples:
    >>> FTP().listdir(path='ftp://ftp.pjm.com/oasis')

    """

    def __init__(self, host_or_url='', user='', passwd='', acct='', timeout=None,
                 source_address: tuple = None):
        """
        :param host: host can receive either a host or a full ftp url.  If a full
                     ftp url is provided, host is extracted and updated and the full
                     url or path is stored as self._path.
        :param user: username used for login to ftp server
        :param passwd: password used for login to ftp server
        :param acct:
        :param timeout: specifies a timeout in seconds for blocking operations like the connection attempt (if is not specified, the global default timeout setting will be used).
        :param source_address: is a 2-tuple (host, port) for the socket to bind to as its source address before connecting. The encoding parameter specifies the encoding for directories and filenames.
         The optional timeout parameter source_address
        """
        self.scheme = ''
        self.path = ''
        if host_or_url:
            self.set_url(host_or_url=host_or_url, source_address=source_address)
        super().__init__(host=self.host, user=user, passwd=passwd, acct=acct,
                         timeout=timeout, source_address=source_address)
        # self.session(self.host, user=user, passwd=passwd, acct=acct,
        #              timeout=timeout, source_address=source_address)

    @staticmethod
    def url_split(host_or_url, source_address: tuple = None) -> FTPPathParts:
        return url_split(host_or_url=host_or_url, source_address=source_address)

    @staticmethod
    def url_join(scheme, netloc, path='') -> str:
        return url_join(scheme=scheme, netloc=netloc, path=path)

    def dirname(self, host_or_url: str = '') -> str:
        host_or_url = host_or_url or self.path
        return url_split(host_or_url=host_or_url).dirname

    @property
    def url(self) -> str:
        return url_join(self.scheme, self.host, self.path)

    @url.setter
    def url(self, new_url):
        self.set_url(host_or_url=new_url)

    def set_url(self, host_or_url, source_address: tuple = None):
        x = url_split(host_or_url=host_or_url, source_address=source_address)
        assert (x.scheme.lower() in ['ftp', 'ftps', ''])
        self.scheme = x.scheme or self.scheme
        self.host = x.netloc or self.host
        self.path = x.path

    def session(self, host_or_url='', user='', passwd='', acct='',
                timeout=None, source_address=None):
        """
        If a session is not already open, create one.  Attempts FTP.connect
        and FTP.login methods.
        :param host_or_url:
        :param user:
        :param passwd:
        :param acct:
        """
        if timeout: self.timeout = timeout
        if host_or_url or source_address:
            # set self.scheme, .host, .path
            self.set_url(host_or_url, source_address)
        # if self.host
        # if parts.netloc:
        try:
            self.connect()
        except ConnectionRefusedError:
            print()
            if self.source_address:
                self.connect(source_address=self.source_address)
            else:
                self.connect(self.host)
            print()
        except Exception as e:
            raise
        if not self.lastresp == '220':  # connect_response.startswith ('220'):
            raise ConnectionError(self.lastresp)

        # login
        if user or passwd or acct:
            self.login(user=user, passwd=passwd, acct=acct)
        else:
            self.login()

        return self

    def stats(self, url_or_path: str, user='', passwd='', acct='',
              output_option: str = '') -> Union[StatsTuple, int, dtdt, NoneType]:
        """
        Get the name of a file's containing directory, basename, modified time, and file size

        :param url_or_path:     The url or path of the file. If only providing the path,
                            then you must also provide an ftp_session.
        :param output_option:  status_tuple, "size_only", "modified_only",
                               "dirname_only",  "basename_only" or "split_path_only"
        :param user:    ftp username
        :param passwd:  ftp password
        :param acct:    ftp account
            :return: if no kwargs provided, returns a StatusTuple (a named tuple as
                 defined in this function).  If a kwarg is provided, then a single
                 value is returned of the appropriate type.
        """

        # make sure we have an active session
        parts = url_split(url_or_path)
        if parts.netloc:
            # url_or_path includes ftp host info
            self.session(url_or_path, user=user, passwd=passwd, acct=acct)
        else:
            # url_or_path does not include ftp host info
            self.session()

        parts = FTPPathParts(self.scheme, parts.netloc or self.host, parts.path or self.path,
                             parts.dirname, parts.basename, parts.url)

        # verify path exists
        if not self.exists(parts.path):
            raise FileNotFoundError

        # now that we are logged into the ftp server, let's double check that
        # we split dirname and basename correctly.
        if self.is_dir(parts.path):
            _dirname, _basename = parts.path, ''
        else:
            _dirname, _basename = os.path.split(parts.path)

        # get modified date
        _mod_time = None
        if output_option.lower() != 'size_only':
            try:
                _mod_time = parser.parse(self.voidcmd(f"MDTM {parts.path}")[4:].strip())
            except ftplib.error_perm:
                _mod_time = None
            except Exception:
                raise

        # get file size
        _size = None
        if output_option.lower != 'modified_only':
            try:
                _size = super().size(parts.path)
            except ftplib.error_perm:
                _size = None
            except Exception:
                raise

        # return the results
        if output_option.lower() == 'size_only':
            return _size
        elif output_option.lower() == 'modified_only':
            return _mod_time
        else:
            return StatsTuple(self.scheme, self.host, parts.path,
                              _dirname, _basename, _mod_time, _size)

    def modified(self, host_or_url: str = '', user='', passwd='', acct='') -> dtdt:
        host_or_url = host_or_url or self.path
        self.session(host_or_url=host_or_url, user=user,
                     passwd=passwd, acct=acct)
        return self.stats(host_or_url, output_option='modified_only')

    def size(self, host_or_url: str = '', user='', passwd='', acct='') -> int:
        host_or_url = host_or_url or self.path
        parts = url_split(host_or_url=host_or_url)
        path = parts.path
        self.session(host_or_url=host_or_url, user=user,
                     passwd=passwd, acct=acct)
        if parts.basename:
            return super().size(parts.path)
        else:
            return None

    def exists(self, path: str) -> bool:
        # if scheme or host are included in path, we'll strip those out.
        self.session()
        parts = url_split(path)
        # x = self.voidcmd (f"MDTM {parts.path.rstrip('/')}")
        try:
            x = self.nlst(parts.path.rstrip('/'))
            return True
        except ftplib.error_perm:
            try:
                x = self.nlst(parts.dirname.strip('/'))
                return True
            except ftplib.error_perm as e:
                print(f"Error getting NLIST of {parts.dirname}.  ", e)
                return False
        except Exception:
            raise

    # def download(self, url_or_path: str, user='', passwd='', acct='',
    #              tgt_folder='', overwrite: bool = True) -> GetTuple:
    #
    #     parts = url_split(url_or_path)
    #     if parts.netloc:
    #         # set_url will accept new scheme and host from url_or_path if provided;
    #         # else, the existing self.scheme and .host are kept.
    #         self.set_url(url_or_path)
    #         # parts.path = self.path
    #         parts = FTPPathParts(self.scheme, self.host, parts.path,
    #                              parts.dirname, parts.basename, parts.url)
    #
    #     # open and log into ftp
    #     self.session(self.host, user=user, passwd=passwd, acct=acct)
    #
    #     # verify path exists
    #     if not self.exists(parts.path):
    #         raise FileNotFoundError
    #     # get file stats from server before downloading
    #     stats = self.stats(url_or_path=url_or_path)
    #
    #     # download file from ftp server to disk
    #     save_as = stats.path
    #     if tgt_folder:
    #         save_as = os.path.join(tgt_folder, stats.basename)
    #     if not overwrite and os.path.exists(save_as):
    #         raise FileExistsError(f'File "{save_as}" already exists. ')
    #
    #     with open(save_as, "wb") as file:
    #         # use FTP's RETR command to download the file
    #         self.retrbinary(f"RETR {stats.path}", file.write)
    #
    #     return GetTuple(stats.scheme, stats.netloc, stats.path, stats.dirname,
    #                     stats.basename, stats.modified, stats.size, save_as)
    #
    def download(self, url_or_path: str, user='', passwd='', acct='',
                 tgt_folder='', overwrite: bool = True) -> GetTuple:

        # get file stats from server before downloading
        result = self.stats(url_or_path=url_or_path, user=user, passwd=passwd, acct=acct)
        # download file from ftp server to disk
        save_as = pathlib.Path(result.path).name
        if tgt_folder:
            save_as = os.path.join(tgt_folder, result.basename)
        if not overwrite and os.path.exists(save_as):
            raise FileExistsError(f'File "{save_as}" already exists. ')

        with open(save_as, "wb") as file:
            # use FTP's RETR command to download the file
            _global_ftp.retrbinary(f"RETR {result.path}", file.write)

        return GetTuple(result.scheme, result.netloc, result.path, result.dirname,
                        result.basename, result.modified, result.size, save_as)

    def is_dir(self, path: str) -> bool:
        # self.session()
        # if scheme or host are included in path, we'll strip those out.
        path = urlsplit(path).path
        if not self.exists(path=path):
            return False
        try:
            orig_dir = self.pwd()
            self.cwd(path)
            self.cwd(orig_dir)
            return True
        except ftplib.error_perm as e:
            return False
        except Exception as e:
            raise e

    def listdir(self, path: str, get_stats: bool = False,
                user='', passwd='', acct='') -> list:
        """
        Return a directory listing of path.
        :param path: may be a path within the url or the full url
        :param user: username
        :param passwd: password
        :param acct: ftp account
        :param get_stats:
        :return: namedtuple(is_dir, dirs, nondirs), where
                is_dir = True if ftp_path is a dir (not a file or other)
                         False if ftp_path is not a dir
                dirs = list of directories in ftp_path
                non_dirs = list of non-directory items in ftp_path
        """
        ListTuple = namedtuple('ListTuple', ['name', 'modified',
                                             'size', 'is_dir'])
        # open and log into ftp
        try:
            self.session()
        except:
            self.session(host_or_url=path, user=user, passwd=passwd, acct=acct)
        if get_stats:
            raise NotImplementedError

        file_list, dirs, non_dirs = [], [], []
        res = []

        parts = urlsplit(path)

        self.retrlines(f'LIST {parts.path}',
                       lambda s: file_list.append(s.split()))
        # PJM ftp servers do not support mlsd, so this substandard workaround
        # is necessary.
        for info in file_list:
            if os.name == 'nt':
                # info[1] = date
                # info[2] = time
                # info[-2] = type or size
                # info[-1] = name
                mod_time = info[0] + ' ' + info[1]
                mod_time = dtdt.strptime(mod_time, '%m-%d-%y %I:%M%p')
                if info[-2].upper() in ['<DIR>']:
                    # info[-2] = type
                    #           [name,     modified, size]
                    # ['name', 'modified','size', 'is_dir']
                    res.append(ListTuple(info[-1], mod_time, None, True))
                elif info[-2].isnumeric:
                    # info[-2] = size
                    #               [name,     modified, size    ]
                    res.append(ListTuple(info[-1], mod_time,
                                         int(info[-2]), False))
                else:
                    #               [name,     modified, size    ]
                    res.append(ListTuple(info[-1], mod_time, None, None))
            else:
                # Not tested on non-NT systems.
                # info[0] = type
                # info[-1] = name
                ls_type, name = info[0], info[-1]
                _is_dir = False
                if ls_type.startswith('d'):
                    _is_dir = True
                res.append(ListTuple(name, None, None, _is_dir))

        return res

    def walk(self, top, path=''):
        raise NotImplementedError
        # TODO: this fails on at "self.retrlines (f'LIST {parts.path}',
        # # lambda s: file_list.append (s.split ()))" in self.listdir
        contents = self.listdir(top)
        dirs = [x.name for x in contents if x.is_dir()]
        nondirs = [x.name for x in contents if not x.is_dir()]
        yield (path or top), dirs, nondirs
        path = top
        for name in dirs:
            path = os.path.join(path, name)
            for x in self.walk(name, path):
                yield x
            self.cwd('..')
            path = os.path.dirname(path)


# ##############################################################################
# API - Functions
# ##############################################################################

_global_ftp = FTP()


def exists(ftp_url: str, user='', passwd='', acct=''):
    global _global_ftp
    _global_ftp.session(host_or_url=ftp_url, user=user, passwd=passwd, acct=acct)
    return _global_ftp.exists(path=ftp_url)


def new_session(ftp_url: str, user='', passwd='', acct='',
                timeout=None, source_address=None) -> FTP:
    global _global_ftp
    i = 0
    while i < 3:
        try:
            host = ftp_url or _global_ftp
            _global_ftp = FTP(host_or_url=host,
                              user=user, passwd=passwd,
                              acct=acct, timeout=timeout,
                              source_address=source_address)
            _global_ftp.connect()
            _global_ftp.login(user=user, passwd=passwd,
                              acct=acct)
            return _global_ftp
        except Exception as e:

            i += 1
            if i >= 2:
                raise e


def stats(url_or_path: str, user='', passwd='', acct='', output_option: str = '') -> StatsTuple:
    """
    Get the name of a file's containing directory, basename, modified time, and file size
    :param url_or_path:     The url or path of the file. If only providing the path,
                        then you must also provide an ftp_session.
    :param user:    ftp username.  ignored if ftp_session != None
    :param passwd:      ftp password.  ignored if ftp_session != None
    :param acct:    ftp account.  ignored if ftp_session != None
    :param output_option:  status_tuple, "size_only", "modified_only",
                           "dirname_only",  "basename_only" or "split_path_only"
    :return: if no kwargs provided, returns a StatusTuple (a named tuple as
             defined in this function).  If a kwarg is provided, then a single
             value is returned of the appropriate type.
    """
    global _global_ftp
    # _global_ftp = new_session()
    return _global_ftp.stats(url_or_path=url_or_path, user=user, passwd=passwd,
                             acct=acct, output_option=output_option)


def basename(path: str, user='', passwd='', acct='', verify=False) -> StatsTuple:
    if verify:
        global _global_ftp
        return stats(url_or_path=path, user=user, passwd=passwd, acct=acct,
                     output_option='basename_only')
    else:
        return url_split(path).basename


def dirname(path: str, user='', passwd='', acct='', verify=False) -> StatsTuple:
    if verify:
        global _global_ftp
        return stats(url_or_path=path, user=user, passwd=passwd, acct=acct,
                     output_option='dirname_only')
    else:
        return url_split(host_or_url=path).dirname


def modified(url_or_path: str, user='', passwd='', acct='') -> StatsTuple:
    global _global_ftp
    return stats(url_or_path=url_or_path, user=user, passwd=passwd, acct=acct,
                 output_option='modified_only')


def size(url: str, user='', passwd='', acct='') -> int:
    global _global_ftp
    return _global_ftp.size(host_or_url=url, user=user, passwd=passwd, acct=acct)


def download(url_or_path: str, user='', passwd='', acct='',
             tgt_folder='', overwrite: bool = True) -> GetTuple:
    # open ftp session
    global _global_ftp
    return _global_ftp.download(url_or_path=url_or_path,
                                user=user, passwd=passwd, acct=acct,
                                tgt_folder=tgt_folder, overwrite=overwrite)


def compare_to_local(local_path: str, ftp_path: str, user='', passwd='', acct='',
                     hash_check: bool = False) -> CompareTuple:
    """
    Compare a file on an ftp server with a local file.  If hash_check==False,
    then the ftp file does not need to be downloaded.  If hash_check==True, then
    the ftp file is downloaded in order to perform a hash operation, so execution
    may take MUCH longer.
    :param local_path:
    :param ftp_path:
    :param user:
    :param passwd:
    :param acct:
    :param hash_check:
    :return: a namedtuple, CompareTuple, of boolean values:
             - match:   True if (a) hash_check==True and hash check passes OR
                                (b) hash_check==False and modified date, size
                                    and basename match.
             - base_match (bool): do local_path and ftp_path basenames match
    """
    global _global_ftp
    ftp_stats = stats(url_or_path=ftp_path, user=user, passwd=passwd, acct=acct)
    lcl_path = os.path.abspath(local_path)
    lcl_folder, lcl_basename = os.path.split(lcl_path)

    base_match = lcl_basename == ftp_stats.basename
    size_match = os.path.getsize(lcl_path) == ftp_stats.size
    modified_match = os.path.getmtime(lcl_path) == ftp_stats.modified
    if hash_check:
        with tempfile.TemporaryDirectory() as fp:
            tmp_folder = str(fp)
            download(url_or_path=ftp_path, user=user, passwd=passwd, acct=acct,
                     tgt_folder=tmp_folder)
            tmp_path = os.path.join(tmp_folder, ftp_stats.basename)
            h_match = hash_match(lcl_path, tmp_path)
        match = h_match
    else:
        h_match = None
        match = all([base_match, size_match, modified_match])

    return CompareTuple(match, base_match, size_match, modified_match, h_match)


def listdir(path: str, user='', passwd='', acct='',
            ftp_session=None, get_stats: bool = False) -> list:
    """
    Return a directory listing of path.
    :param path: may be a path within the url or the full url
    :param user: username
    :param passwd: password
    :param acct: ftp account
    :param ftp_session: an active ftp connection that is logged in.
    :param get_stats:
    :return: namedtuple(is_dir, dirs, nondirs), where
            is_dir = True if ftp_path is a dir (not a file or other)
                     False if ftp_path is not a dir
            dirs = list of directories in ftp_path
            non_dirs = list of non-directory items in ftp_path
    """
    if get_stats:
        raise NotImplementedError

    ListTuple = namedtuple('ListTuple', ['name', 'modified', 'size', 'is_dir'])
    file_list, dirs, non_dirs = [], [], []
    res = []

    # open and log into path
    ftp = ftp_session
    if not ftp_session:
        ftp = new_session(ftp_url=path, user=user, passwd=passwd, acct=acct)

    parts = urlsplit(path)

    ftp.retrlines(f'LIST {parts.path}', lambda s: file_list.append(s.split()))
    for info in file_list:
        if os.name == 'nt':
            # info[1] = date
            # info[2] = time
            # info[-2] = type or size
            # info[-1] = name
            mod_time = info[0] + ' ' + info[1]
            mod_time = dtdt.strptime(mod_time, '%m-%d-%y %I:%M%p')
            if info[-2].upper() in ['<DIR>']:
                # info[-2] = type
                #           [name,     modified, size]
                # ['name', 'modified','size', 'is_dir']
                res.append(ListTuple(info[-1], mod_time, None, True))
            elif info[-2].isnumeric:
                # info[-2] = size
                #               [name,     modified, size    ]
                res.append(ListTuple(info[-1], mod_time, int(info[-2]), False))
            else:
                #               [name,     modified, size    ]
                res.append(ListTuple(info[-1], mod_time, None, None))
        else:
            # Not tested on non-NT systems.
            # info[0] = type
            # info[-1] = name
            ls_type, name = info[0], info[-1]
            is_dir = False
            if ls_type.startswith('d'):
                is_dir = True
            res.append(ListTuple(name, None, None, is_dir))

    return res


def is_dir(path: str, user='', passwd='', acct='',
           ftp_session=None) -> bool:
    """

    :param path: path on the ftp server
    :type path: str
    :param user: ftp username
    :type user: str
    :param passwd: ftp password
    :type passwd: str
    :param acct: ftp account
    :type acct: str
    :param ftp_session:  FTP.session.  If None, new session created.
    :type ftp_session: FTP.session
    :return: True if path is a directory, else False
    :rtype: bool
    """
    # open and log into path
    ftp = ftp_session
    if not ftp_session:
        ftp = new_session(ftp_url=path, user=user, passwd=passwd, acct=acct)
    parts = urlsplit(path)
    try:
        orig_dir = ftp.pwd()
        ftp.cwd(parts.path)
        ftp.cwd(orig_dir)
        return True
    except ftplib.error_perm as e:
        return False
    except Exception as e:
        raise e


def _ftp_class_examples():
    # TODO: Create some examples
    raise NotImplementedError


def _func_examples():
    # TODO: Update examples.  These examples are from before refactoring.
    raise NotImplementedError

    print('\nnew_session:')
    ftp = new_session('ftp://ftp.pjm.com')
    print(ftp.nlst())

    print('\nstats\n', stats('ftp://ftp.pjm.com/oasis'))
    print('\nstats\n', stats('ftp://ftp.pjm.com/oasis/CBMID.pdf'))
    print('\nsplit\n', url_split('ftp://ftp.pjm.com/oasis/CBMID.pdf'))
    print('\nsplit\n', url_join('ftp', 'ftp.pjm.com/', '/oasis/CBMID.pdf'))
    print('\nbasename\n', basename('ftp://ftp.pjm.com/oasis/CBMID.pdf'))
    print('\ndirname\n', dirname('ftp://ftp.pjm.com/oasis/CBMID.pdf'))
    print('\nmodified\n', modified('ftp://ftp.pjm.com/oasis/CBMID.pdf'))
    print('\nsize\n', size('ftp://ftp.pjm.com/oasis/CBMID.pdf'))
    print('\ndownload\n', download('ftp://ftp.pjm.com/oasis/CBMID.pdf',
                                   tgt_folder='C:/temp'))

    print('\nlistdir')
    for row in listdir('ftp://ftp.pjm.com/oasis/CBMID.pdf'):
        print(row)

    print('\nis_dir("ftp://ftp.pjm.com/oasis")\n',
          is_dir('ftp://ftp.pjm.com/oasis'))
    print('\nis_dir("ftp://ftp.pjm.com/oasis/CBMID.pdf")\n',
          is_dir('ftp://ftp.pjm.com/oasis/CBMID.pdf'))

    print('\nurl_split("ftp://ftp.pjm.com/folder1/folder2/file.ext")\n',
          url_split('ftp://ftp.pjm.com/folder1/folder2/file.ext'))


if __name__ == '__main__':
    # _func_examples()
    # _ftp_class_examples()
    pass
