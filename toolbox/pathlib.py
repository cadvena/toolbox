# import sys
import datetime
import warnings
from typing import *

import os
# from os.path import *
import pathlib
from pathlib import *
import shutil
# from shutil import *

from collections import namedtuple, deque
from types import GeneratorType
from toolbox.error_handler import ErrorHandler
from toolbox.swiss_army import py_ver  # , namedtuple2dict
from datetime import datetime as dtdt

TYPE_DICT = {
    # ancestor folder {level} levels up exits.path_name can be used for
    # a new  folder or file.
    3: 'ancestor folder {level} levels up exits.path_name can be ' +
       'used for a new  folder or file.',
    2: 'parent dir "{path_name}" exists; path_name can be used for a ' +
       'new folder or file.',
    1: 'folder',
    0: 'file',
    -1: 'Error: path_name must be a non-zero length string',
    -2: 'Error: invalid path; must contain a valid root dir this ' +
        'indicates that path_name could be used for a new folder or ' +
        'file.',
    -3: 'Error: invalid path name; a sub-folder name is an existing FILE'
    }

default_find_implied = True
default_make_assumptions = True

# ##############################################################################
# pathlib.Path wrapper
# ##############################################################################

class Path(pathlib.Path):
    """Adds some nice stuff on top of `pathlib.Path`
    https://docs.python.org/3/library/pathlib.html#

    ----------------------------------------------------------------------------
    Methods:
    ----------------------------------------------------------------------------
    absolute():     returns absolute path
    cwd():          returns os.getcwd()
    home():         returns newPath object of of user’s home directory
    stat():         Return a os.stat_result object containing information about this path.
    chmod(mode):    Change the file mode and permissions, like os.chmod()
    exists():       Whether the path points to an existing file or directory
    expanduser():   Return a new path with expanded ~ and ~user constructs,
                    as returned by os.path.expanduser()
    getsize()       Return the size, in bytes, of path. Raise OSError if the file does not exist or is inaccessible.
                    https://docs.python.org/3/library/os.path.html#os.path.getsize
    glob(pattern):  Glob the given relative pattern in the directory represented
                    by this path, yielding all matching files (of any kind):
    group():        Return the name of the group owning the file
    is_dir():       Return True if the path points to a directory
    is_file()       Return True if the path points to a regular file
    is_mount()      Return True if the path is a mount point
    is_symlink()    Return True if the path points to a symbolic link, False otherwise
    is_socket()     Return True if the path points to a Unix socket\
    is_fifo()       Return True if the path points to a FIFO
    is_block_device()   Return True if the path points to a block device
    is_char_device()    Return True if the path points to a character device
    iterdir()       When the path points to a directory, yield path objects of
                    the directory contents
    joinpath(*other)    Calling this method is equivalent to combining the path with each
                        of the other arguments in turn
    lchmod(mode)    Like Path.chmod() but, if the path points to a symbolic link,
                    the symbolic link’s mode is changed rather than its target’s.
    lstat()         Like Path.stat() but, if the path points to a symbolic link,
                    return the symbolic link’s information rather than its target’s.
    match(pattern)      Match this path against the provided glob-style pattern. Return True
                        if matching is successful, False otherwise.
    mkdir(mode=0o777, parents=False, exist_ok=False)
    open(mode='r', buffering=-1, encoding=None, errors=None, newline=None)
                    Open the file pointed to by the path, like the built-in open() function
    owner()         Return the name of the user owning the file.
    read_bytes()    Return the binary contents of the pointed-to file as a bytes object
    read_text(encoding=None, errors=None)
                    Return the decoded contents of the pointed-to file as a string:
    readlink()      Return the path to which the symbolic link points
    relative_to(*other)     Compute a version of this path relative to the path represented
                            by other.
    rename(target)  Rename this file or directory to the given target, and return a
                    new Path instance pointing to target.
    replace(target) Rename this file or directory to the given target, and return a new
                    Path instance pointing to target. If target points to an existing
                    file or directory, it will be unconditionally replaced.
    resolve(strict=False)       Make the path absolute, resolving any symlinks.
                                A new path object is returned
    rglob(pattern)  This is like calling Path.glob() with “**/” added in front of the
                    given relative pattern
    rmdir()         Remove this directory. The directory must be empty.
    samefile(other_path)    Return whether this path points to the same file as other_path,
                    which can be either a Path object, or a string.
    size()          Alias for getsize()
    symlink_to(target, target_is_directory=False)
                    Make this path a symbolic link to target.
    link_to(target)     Make target a hard link to this path. -- New in Python version 3.8.
    touch(mode=0o666, exist_ok=True)
                    Create a file at this given path. If mode is given, it is combined with
                    the process’ umask value to determine the file mode and access flags.
                    If the file already exists, the function succeeds if exist_ok is true
                    (and its modification time is updated to the current time), otherwise FileExistsError is raised.
    unlink(missing_ok=False)    Remove this file or symbolic link. If the path points
                                to a directory, use Path.rmdir() instead.
    with_name(name)     Return a new path with the name changed. If the original path doesn’t
                        have a name, ValueError is raised
    with_stem(stem)     Return a new path with the stem changed
    with_suffix(suffix)     Return a new path with the suffix changed
    write_bytes(data)           Open the file pointed to in bytes mode, write data to it,
                                and close the file:
    write_text(data, encoding=None, errors=None)
                    Open the file pointed to in text mode, write data to it,
                    and close the file

    ----------------------------------------------------------------------------
    Properties
    ----------------------------------------------------------------------------
    suffix
    parts       A tuple giving access to the path’s various components
    get_drive       A string representing the get_drive letter or name, if any
    root        A string representing the (local or global) root, if any
    anchor      The concatenation of the get_drive and root
    parents     An immutable sequence providing access to the logical ancestors of the path
    parent      The logical parent of the path
    name        A string representing the final path component, excluding the get_drive and
                root, if any  (same as os.path.basename()
    suffix      The file extension of the final component, if any
    suffixes    A list of the path’s file extensions
    stem        The final path component, without its suffix
    s_posix()    Return a string representation of the path with forward slashes (/)
    as_uri()    Represent the path as a file URI. ValueError is raised if the path isn’t absolute.
    is_absolute()    Return whether the path is absolute or not.
    is_reserved()    With PureWindowsPath, return True if the path is considered reserved
                     under Windows, False otherwise. With PurePosixPath, False is always returned.
    """ \
        # Aways put these two lines at the top of a class which will have some methods
    # which you want to have error handling
    error_handler = ErrorHandler()
    ignore_errors = error_handler.ignore_errors
    # find_implied = default_find_implied
    # make_assumptions = default_make_assumptions
    prev_wds = deque([os.getcwd()])

    def __new__(cls, *args, **kwargs):
        # Commented code below causes self.find_implied to be a read-only attribute.
        # if cls is Path:
        #     cls = pathlib.WindowsPath if os.name == 'nt' else pathlib.PosixPath
        if os.name == 'nt':
            cls._flavour = pathlib._windows_flavour
        else:
            cls._flavour = pathlib._posix_flavour
        self = cls._from_parts(args)
        if not self._flavour.is_supported:
            raise NotImplementedError("cannot instantiate %r on your system"
                                      % (cls.__name__,))
        # if py_ver < 3.10:  # python 3.10
        self.__init__()
        return self

    def __init__(self, *args, **kwargs):
        self.prev_wds = deque([os.getcwd()])    # TODO: should this be self._str, os.getcwd() or
                                                # an empty dequeue?
        self.ignore_errors = kwargs.pop('ignore_errors', self.ignore_errors)

    @error_handler.wrap(on_error_return = False)
    def is_file(self, make_assumptions = default_make_assumptions) -> bool:

        if not make_assumptions:
            return super().is_file()

        # else: make_assumptions == True
        if self.exists():
            return super().is_file()
        else:  # not exists
            # if suffixes then probably a file, else probably a file
            return len(self.suffixes) > 0

    @error_handler.wrap(on_error_return = False)
    def is_dir(self, make_assumptions = default_make_assumptions) -> bool:
        if not make_assumptions:
            return super().is_dir()
        # else: make_assumptions == True
        if self.exists():
            return super().is_dir()
        else:
            # if no suffixes then probably a dir, else probably a file
            return len(self.suffixes) == 0

    @property
    def drive(self):
        return super().drive

    def get_drive(self, find_implied: bool = default_find_implied):
        """ Like drive property, except with find_implied argument.  If find_implied == True,
        then get drive from absolute path, i.e., Path.absolute().drive
        the absolute path.
        Examples:
            p = Path("folder/stem.suffix")
            p.drive -> ''
            p.get_drive(implied = False) -> p.drive, i.e., ''
            p.get_drive(implied = True) -> p.absolute().drive,
                                           i.e., the drive of the current working directory

            p = Path("C:/folder/stem.suffix")
            p.drive -> 'C:'
            p.get_drive(implied = False) -> p.drive, i.e., 'C:'
            p.get_drive(implied = True) -> p.absolute().drive, i.e., 'C:'
        """
        if find_implied:
            # drv = super().get_drive.strip('/').strip('\\')
            return super().drive or super().absolute().drive
        else:
            return super().drive

    def drive_parent(self, find_implied: bool = default_find_implied):
        """
        Returns string minus self.name.  If self.get_drive == '', then return
        self.absolute() minus self.name.  The result is similar to the first part
        of os.path.split()
        :return: get_drive and parent folder name as a single string
        """
        if find_implied:
            drv = super().drive.strip('/').strip('\\')
            if not drv:
                result = self.absolute().parent
            else:
                result = self.parent
        else:
            result = self.parent
        if not isinstance(result, Path):
            result = Path(result)
        return result

    def folder_part(self, make_assumptions = default_make_assumptions):
        """

        :param make_assumptions:  True: assume that filenames have extensions and folders do not.
                                 False: if self.exists(), then use is_dir and is_file, else,
                                 raise NotImplementedError.

        :return:
        """
        return self.drive_folder(find_implied=False, make_assumptions = make_assumptions)

    def drive_folder(self, find_implied: bool = default_find_implied,
                     make_assumptions = default_make_assumptions):
        if find_implied:
            p = self.absolute()
        else:
            p = self
        drive = self.get_drive(find_implied=False)
        if find_implied and drive == '.':
            result = self.absolute().folder_part(make_assumptions = make_assumptions)
        else:
            if self.is_file(make_assumptions=make_assumptions):
                result = self.parent
            elif self.is_dir(make_assumptions=make_assumptions):
                result = self
            else:
                raise NotImplementedError
            if not isinstance(result, Path):
                result = Path(result)
        # if not isinstance (result, Path): result = Path (result)
        return result

    def drive_folder_exists(self, find_implied: bool = default_find_implied,
                     make_assumptions = default_make_assumptions):
        return self.drive_folder().exists()

    def parent_exists(self):
        return Path(self.parent).exists()

    def info(self, find_implied: bool = default_find_implied,
             make_assumptions = default_make_assumptions, as_dict = False):
        """
        Return intelligent info about self as either a namedtuple (PathInfo)
        or a dict.
        :param find_implied:
        :param make_assumptions:
        :param as_dict:  True: return dict of path info
                        False: return namedtuple, PathInfo, of path info
        :return:
        """
        # If the path exists, then we can assume it is valid.
        PathInfo = namedtuple('PathInfo', ['is_file', 'is_dir', 'absolute', 'drive_folder',
                                           'get_drive', 'folder_part', 'parent', 'name', 'stem',
                                           'suffix', 'suffixes', 'filename_sans_folders'])
        is_file = self.is_file(make_assumptions = make_assumptions)
        filename_sans_folders = name
        if not is_file:
            filename_sans_folders = None
        if as_dict:
            return {
                'is_file': is_file,
                'is_dir': self.is_dir(make_assumptions = make_assumptions),
                'absolute': self.absolute(),
                'drive_folder': self.drive_folder(find_implied = find_implied, make_assumptions =
                make_assumptions),
                'get_drive': self.get_drive(find_implied = find_implied),
                'folder_part': self.folder_part(make_assumptions = make_assumptions),
                'parent': self.parent.str,
                'name': self.name,
                'stem': self.stem,
                'suffix': self.suffix,
                'suffixes': self.suffixes,
                'filename_sans_folders': filename_sans_folders
                }
        else:
            return PathInfo(is_file,
                            self.is_dir(make_assumptions = make_assumptions),
                            self.absolute(),
                            self.drive_folder(find_implied = find_implied, make_assumptions =
                            make_assumptions),
                            self.get_drive(find_implied = find_implied),
                            self.folder_part(make_assumptions = make_assumptions),
                            self.parent.str,
                            self.name,
                            self.stem,
                            self.suffix,
                            self.suffixes,
                            filename_sans_folders
                            )

    def filename_sans_folders(self, make_assumptions = default_make_assumptions):
        if self.is_file(make_assumptions = make_assumptions):
            return self.name
        else:
            return None

    def split(self, make_assumptions = default_make_assumptions):
        if not make_assumptions:
            return os.path.split(self.str)
        else:
            return self.folder_part(make_assumptions = True), \
                   self.filename_sans_folders(make_assumptions = True)

    @error_handler.wrap(on_error_return = False)
    def mkdir(self, mode = 511, parents = False, exist_ok = False,
              force_replace: bool = False) -> bool:
        """
        Path.mkdir(mode=511, parents=True, exist_ok=True)
        Create a new directory at this given path.
        :param mode: If mode is given (default = 511), it is combined with the process’ umask
                    value to determine the file mode and access flags.
        :param parents:
                    True: missing parents of this path are created as needed; they are created with
                            the default permissions without taking mode into account (mimicking the
                            POSIX mkdir -p command).
                    False (default): a missing parent raises FileNotFoundError.
        :param exist_ok:
                    True: FileExistsError exceptions will be ignored (same behavior as the
                            POSIX mkdir -p command), but only if the last path component is not an
                            existing non-directory file.
                    False (default): if path exists, return False.

        :param force_replace: if the folder already exists, delete it and all its contents,
                              then recreate as an empty folder.
        :return: True is path created in accordance with specified parameters, else returns False.
        """
        if force_replace and self.exists() and self.is_dir:
                self.rmtree()
        super().mkdir(mode = mode, parents = parents, exist_ok = exist_ok)
        return self

    @error_handler.wrap(on_error_return = False)
    def mk_parent(self, mode = 511, parents = True, exist_ok = True) -> bool:
        self.parent.mkdir(mode = mode, parents = parents, exist_ok = exist_ok)
        return self

    @error_handler.wrap(on_error_return = False)
    def mk_folder_part(self, mode = 511, parents = True, exist_ok = True,
                       make_assumptions = default_make_assumptions) -> bool:

        fldr = self.folder_part(make_assumptions = make_assumptions)
        if type(fldr) == str: fldr = Path(fldr)
        fldr.mkdir(mode = mode, parents = parents, exist_ok = exist_ok)
        return fldr

    @error_handler.wrap(on_error_return = False)
    def mkdir_or_replace(self, mode = 511, force_replace: bool = True) -> bool:
        """
        Create new directory or replace existing directory with new empty directory.
        :param mode:
        :param parents: True/False
                True: any missing parents of this path are created as needed
                False: a missing parent raises FileNotFoundError.
        """
        return self.mkdir(mode = mode, parents = True, exist_ok = True,
                          force_replace = force_replace)

    @error_handler.wrap(on_error_return = False)
    def chdir(self) -> bool:
        """
        Change the current working directory to self.  And,
        save the previous working directory to our prev_wds deque. """
        if self == self.cwd():
            # self is the current directory, so nothing to do
            return True
        # get the name of the curr working dir before we change dirs.
        init_wd = os.getcwd()
        # change directories
        os.chdir(self.str)
        # if we didn't error out and init_wd is not already the last item in
        # self.prev_wds, then save init_wd to our self.prev_wds deque.
        if self.prev_wds[-1] != init_wd:
            self.prev_wds.append(init_wd)
        return self

    @error_handler.wrap(on_error_return = False)
    def ch_prev_dir(self) -> bool:
        """
        Move to the prior working directory from the deque.
        :return:
        """
        if len(self.prev_wds) == 0:
            raise AttributeError('No previous working directories are known.')
        else:
            # change to the previous working dir
            os.chdir(self.prev_wds[-1])

            # only after successfully changing dirs do we remove the prev
            # working dir from the deque.
            # TODO: should we pop or rotate the deque?
            # self.prev_wds.pop()
            self.prev_wds.rotate()
        return self

    def listdir(self, ret_Path: bool = True) -> list:
        """Lists directories and files immediately in directory
        Consider using .iterdir() method instead, which is a generator function."""
        result = os.listdir(self.str)
        if ret_Path:
            result = [Path(p) for p in result]
        return result

    def walk(self, pattern='*') -> Iterator['Path']:
        for p in self.rglob(pattern = pattern):
            yield Path(p)

    def walk_files(self) -> Iterator['Path']:
        for root, dirs, files in os.walk(self.str):
            for fn in files:
                yield Path(root) / fn

    def walk_dirs(self) -> Iterator['Path']:
        for root, dirs, files in os.walk(self.str):
            for d in dirs:
                yield Path(root) / d

    @error_handler.wrap(on_error_return = False)
    def rmtree(self) -> bool:
        shutil.rmtree(self.str)
        return True
        # if not self.is_dir() and not self.is_file():
        #     # Warn instead of removing if removing a directory that does not exist
        #     warnings.warn (f"Tried to remove directory but it does not exist: {self.str}")
        #     return
        # return shutil.rmtree(self.str)

    @error_handler.wrap(on_error_return = False)
    def remove(self) -> bool:
        if self.is_file():
            self.unlink()
        else:
            self.rmdir()
        return True

    delete = remove

    @error_handler.wrap(on_error_return = False)
    def copy(self, sink: Union[str, 'Path', pathlib.Path]) -> bool:
        if self.is_file():
            shutil.copy(self.str, str(sink))
        else:
            shutil.copytree(self.str, str(sink))
        return True

    @error_handler.wrap(on_error_return = False)
    def move(self, sink: Union[str, 'Path', pathlib.Path]) -> bool:
        if self.is_file():
            shutil.move(self.str, str(sink))
        else:
            shutil.copytree(self.str, str(sink))
            shutil.rmtree(self.str)
        return True

    def relative_to(self, *other):
        return Path(super(Path, self).relative_to(*other))

    @property
    def str(self):
        # return super().__str__()
        return str(self)

    @property
    @error_handler.wrap(on_error_return = None)
    def modify_time(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(os.path.getmtime(self.str))

    @property
    @error_handler.wrap(on_error_return = None)
    def create_time(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(os.path.getctime(self.str))

    def __truediv__(self, key):
        return super(Path, self).__truediv__(key)

    def __rtruediv__(self, key):
        return super(Path, self).__rtruediv__(key)

    @error_handler.wrap(on_error_return = False)
    def getsize(self):
        return os.path.getsize(self)

    size = getsize

    @error_handler.wrap(on_error_return = False)
    def chmod(self, mode):
        return super().chmod(mode = mode)

    @error_handler.wrap(on_error_return = False)
    def lchmod(self, mode):
        return super().lchmod(mode = mode)

    @error_handler.wrap(on_error_return = False)
    def rename(self, target):
        super().rename(target = target)
        return True

    @error_handler.wrap(on_error_return = False)
    def unlink(self):
        super().unlink()
        return True

    @error_handler.wrap(on_error_return = False)
    def rmdir(self):
        super().rmdir()
        return True

    @error_handler.wrap(on_error_return = False)
    def touch(self, mode = 438, exist_ok = True):
        super().touch(mode, exist_ok)
        return True

    @error_handler.wrap(on_error_return = False)
    def symlink_to(self, target, target_is_directory = False):
        return super().symlink_to(target, target_is_directory = target_is_directory)

    @error_handler.wrap(on_error_return = False)
    def hardlink_to(self, target):
        if py_ver < 3.10:
            return self.link_to(target)
        return super().hardlink_to(target)

    @error_handler.wrap(on_error_return = False)
    def link_to(self, target):
        if py_ver < 3.08:
            if self.is_file(make_assumptions = False):
                return self.symlink_to(target, target_is_directory = True)
            else:
                return self.symlink_to(target, target_is_directory = False)
        elif py_ver >= 3.10:
            warnings.warn("""link_to() deprecated since version 3.10: This method is deprecated in 
            favor of Path.hardlink_to(), as the argument order of Path.link_to() does not match that 
            of Path.symlink_to().""")
        return super().link_to(target)

    @error_handler.wrap(on_error_return = False)
    def joinpath(self, *args):
        return super().joinpath(*args)

    @error_handler.wrap(on_error_return = False)
    def write_text(self, data, encoding = None, errors = None):
        return super().write_text(data = data, encoding = encoding, errors = errors)

    @error_handler.wrap(on_error_return = False)
    def write_bytes(self, data):
        return super().write_bytes(data = data)

    @staticmethod
    @error_handler.wrap(on_error_return = False)
    def copyfile(src, dst, follow_symlinks = True, try_hard: bool = True):
        return _copy_file(src, dst, follow_symlinks = follow_symlinks, try_hard = try_hard)

    def backup(self, backup_folder = None, utc = True):
        """
        Create a backup copy of the file.  Makes a copy fo the folder or file
        with a timestamp added to the filename to distinguish it.
        :param backup_folder: Optionally specify a folder for the backup.  If not specified,
                              the backup will be in the same location as self.
        :param utc: if True, timestamp string is UTC,
                    if False, timestamp string is in local time.
        :return: Path object representing the backup file.
        """

        def timestamp_str(utc = True):
            f = dtdt.utcnow if utc else dtdt.now
            if utc:
                return f().isoformat()[:19].replace(".", "_").replace(":", "-")
            else:
                return f().isoformat()[:19].replace(".", "_").replace(":", "-")

        if not self.exists():
            return False
        elif self.is_dir() or self.is_file():
            bck = timestamp_str(utc = utc)
            bck = self.with_name(self.name + "_" + bck + self.suffix)
            assert (not os.path.exists(bck))
            if self.is_dir():
                shutil.copytree(src = self, dst = bck)
            else:  # self.is_file()
                shutil.copyfile(src = self, dst = bck)
        else:
            raise NotImplementedError
        return Path(bck)


PathType = type(Path)

# ##############################################################################
# shutil utilities
# https://docs.python.org/3/library/shutil.html
# ##############################################################################

# under imports, we issued: from shutil import *

# copy = shutil.copy
chown = shutil.chown
change_owner = shutil.chown  # os.chroot(path): Change the root directory of the current process to path.
copytree = shutil.copytree
rmtree = shutil.rmtree
move = shutil.move
which = shutil.which
"""
shutil file operations:
copyfileobj(fsrc, fdst[, length])    
    Copy the contents of the file-like object fsrc to the file-like object fdst.
copyfile(src, dst, *, follow_symlinks=True) 
    Copy the contents (no metadata) of the file named src to a file 
    named dst and return dst in the most efficient way possible.
copymode(src, dst, *, follow_symlinks=True) Copy the permission bits from src to dst.
copystat(src, dst, *, follow_symlinks=True)
    Copy the permission bits, last access time, last modification time, and flags 
    from src to dst.
ignore_patterns(*patterns)
    This factory function creates a function that can be used as a callable for copytree()’s ignore argument, 
copytree(src, dst, symlinks=False, ignore=None, copy_function=copy2,
         ignore_dangling_symlinks=False, dirs_exist_ok=False)
    Recursively copy an entire directory tree rooted at src to a directory named 
    dst and return the destination directory.
rmtree(path, ignore_errors=False, onerror=None)
    Delete an entire directory tree; path must point to a directory (but not a 
    symbolic link to a directory).
move(src, dst, copy_function=copy2)
    Recursively move a file or directory (src) to another location (dst) and 
    return the destination.
disk_usage(path)
    Return disk usage statistics about the given path as a named tuple with the 
    attributes total, used and free
chown(path, user=None, group=None)
which(cmd, mode=os.F_OK | os.X_OK, path=None)
    Return the path to an executable which would be run if the given cmd was 
    called. If no cmd would be called, return None.
"""

# ##############################################################################
# functions that are wrappers of shutil functions
# ##############################################################################
import shutil

rm_tree = shutil.rmtree
del_tree = shutil.rmtree
copy_tree = shutil.copytree
move = shutil.move
which = shutil.which
disk_usage = shutil.disk_usage


def copy(src, dst, follow_symlinks = True, preserve_file_meta: bool = True):
    """
    Extends shutil.copyfile (https://docs.python.org/3/library/shutil.html) to
    attempt to create the destination folder if it does nto exist.

    Copies the file src to the file or directory dst. src and dst should be path-like objects or strings. If dst specifies a directory, the file will be copied into dst using the base filename from src. Returns the path to the newly created file.

    If follow_symlinks is false, and src is a symbolic link, dst will be created as a symbolic link. If follow_symlinks is true and src is a symbolic link, dst will be a copy of the file src refers to.

    copy() copies the file data and the file’s permission mode (see os.chmod()). Other metadata, like the file’s creation and modification times, is not preserved. To preserve all file metadata from the original, use copy2() instead.

    Raises an auditing event shutil.copyfile with arguments src, dst.

    Raises an auditing event shutil.copymode with arguments src, dst.

    Changed in version 3.3: Added follow_symlinks argument. Now returns path to the newly created file.

    Changed in version 3.8: Platform-specific fast-copy syscalls may be used internally in order to copy the file more efficiently. See Platform-dependent efficient copy operations section.
    :param src:
    :param dst:
    :param follow_symlinks:
    :return:
    """
    d = Path(dst)
    d.mkdir(parents = True, exist_ok = True)
    dst_folder = parse_path(dst).drive_folder
    status, msg = mkdir(dst_folder)
    if status < 0:
        msg = f'Error copying file "{src}" to "{dst}". ' + \
              f'Unable to create destination folder, ' + \
              f'"{dst_folder}". {msg}'
        raise OSError(msg)

    try:
        if preserve_file_meta:
            shutil.copy2(src = src, dst = dst, follow_symlinks = follow_symlinks)
        else:
            shutil.copy(src = src, dst = dst, follow_symlinks = follow_symlinks)
        return 0, 'Success'
    except Exception as e:
        msg = f'Error copying file "{src}" to "{dst}". {str(e)}'
        raise Exception(msg)


def copyfile(src, dst, follow_symlinks = True, try_hard: bool = True):
    """
    Extends shutil.copyfile (https://docs.python.org/3/library/shutil.html) to
    attempt to create the destination folder if it does nto exist.

    Copy the contents (no metadata) of the file named src to a file named dst and return dst in the most efficient way possible. src and dst are path-like objects or path names given as strings.

    dst must be the complete target file name; look at copy() for a copy that accepts a target directory path. If src and dst specify the same file, SameFileError is raised.

    The destination location must be writable; otherwise, an OSError exception will be raised. If dst already exists, it will be replaced. Special files such as character or block devices and pipes cannot be copied with this function.

    If follow_symlinks is false and src is a symbolic link, a new symbolic link will be created instead of copying the file src points to.

    Raises an auditing event shutil.copyfile with arguments src, dst.

    Changed in version 3.3: IOError used to be raised instead of OSError. Added follow_symlinks argument. Now returns dst.

    Changed in version 3.4: Raise SameFileError instead of Error. Since the former is a subclass of the latter, this change is backward compatible.

    Changed in version 3.8: Platform-specific fast-copy syscalls may be used internally in order to copy the file more efficiently. See Platform-dependent efficient copy operations section.
    :param try_hard:
    :param src:
    :param dst:
    :param follow_symlinks:
    :return:
    """
    # confirm src exists
    if not os.path.exists(src):
        raise FileNotFoundError(f'File src <"{str(src)}"> does not exist')

    # Create destination folder
    src_filename_sans_folders = Path(src, find_implied = try_hard,
                                     make_assumptions = try_hard
                                     ).info().filename_sans_folders
    d = Path(dst, find_implied = try_hard, make_assumptions = try_hard)
    d_info = d.info(as_dict = True)
    if not src_filename_sans_folders:
        # src does not have a determinable filename_sans_folders
        d_info['folder_part'] = str(d.parent)
        d_info['filename_sans_folders'] = d_info.name

    if try_hard and not os.path.exists(d_info['folder_part']):
        pathlib.Path(d_info['folder_part']).mkdir(mode = stat.S_IWRITE,
                                                  parents = True,
                                                  exist_ok = True)
    # begin copy
    try:
        shutil.copyfile(src = src, dst = dst, follow_symlinks = follow_symlinks)
        return 0, 'Success'
    except Exception as e:
        msg = f'Error copying file "{src}" to "{dst}". {str(e)}'
        raise Exception(msg)
    return Path(dst)


_copy_file = copyfile

# chown also exists under os
# change_owner = shutil.chown

ShutilError = shutil.Error
# This exception collects exceptions that are raised during a multi-file
# operation. For copytree(), the exception argument is a list of 3-tuples
# (srcname, dstname, exception).

# ##############################################################################
# os.path
# https://docs.python.org/3/library/os.path.html
# ##############################################################################
"""
abs_path(path)      os.path.abs_path(path): Return a normalized absolutized version of the pathname 
path.
basename(path)      os.path.basename(path): basename('/foo/bar/') -> 'bar'
                    basename('folder/folder2/file.ext') -> 'file.ext'
commonpath(paths)   os.path.commonpath(paths): Return the longest common sub-path of each pathname in the 
                    sequence paths
commonprefix(list)  commonprefix(list): Return the longest path prefix (taken character-by-character) 
                    that is a prefix of all paths in list.
dirname(path)       Eee custom function, dirname below
exists(path)        os.path.: True if path refers to an existing path
                    False if 
                        1 path does not exist 
                        2 broken symbolic link
                        3 may return false if execute permissions not granted
lexists(path)       os.path.lexists(path): True if
                        1 path refers to an existing path
                        2 broken symbolic link
                    False if 
                        1 path does not exist 
                        2 may return false if execute permissions not granted
expanduser(path)    os.path.expanduser(path): On Unix and Windows, return the argument with an initial 
                    component of ~ or ~user replaced by that user’s home directory.
expandvars(path)    os.path.expandvars(path): Return the argument with environment variables expanded. 
getatime(path)      os.path.getatime(path): Return the time of last access of path
getctime(path)      os.path.getctime(path): Return the system’s ctime which, on some systems (like Unix) 
                    is the time of the last metadata change, and, on others 
                    (like Windows), is the creation time for path.
getsize(path)       os.path.getsize(path): Return the size, in bytes, of path. 
isabs(path)         os.path.isabs(path): Return True if path is an absolute pathname.
isfile(path)        os.path.isfile(path): Return True if path is an existing regular file.
sdir(path)          os.path.sdir(path): Return True if path is an existing directory. 
islink(path)        os.path.islink(path): Return True if path refers to an existing directory
                    entry that is a symbolic link.
ismount(path)       os.path.ismount(path): Return True if pathname path is a mount point:
join()              os.path.join
normpath(path)      os.path.normpath(path): Normalize a pathname by collapsing redundant 
                    separators and up-level references so that A//B, A/B/, A/./B and 
                    A/foo/../B all become A/B. 
relpath(path, start=os.curdir)       os.path.relpath(path, start=os.curdir) : 
                    Return a relative filepath to path either from the current directory or 
                    from an optional start directory.                     
samefile(path1, path2)  os.path.samefile(path1, path2):
                    Return True if both pathname arguments refer to the same file or directory.
sameopenfile(fp1, fp2)  os.path.sameopenfile(fp1, fp2):
                    Return True if the file descriptors fp1 and fp2 refer to the same file.
samestat(stat1, stat2)  os.path.samestat(stat1, stat2):
                    Return True if the stat tuples stat1 and stat2 refer to the same file.
split(path)         os.path.split(path): Split the pathname path into a pair, (head, tail) 
splitdrive(path)    os.path.splitdrive(path): Split the pathname path into a pair (get_drive, tail) 
splitext(path)      os.path.splitext(path): Split the pathname path into a pair (root, ext) 
                    such that root + ext == path, and the extension, ext, is empty or begins 
                    with a period and contains at most one period.
supports_unicode_filenames      os.path.supports_unicode_filenames:
                    True if arbitrary Unicode strings can be used as file names (within limitations imposed by the file system).

"""

abspath = os.path.abspath
basename = os.path.basename
commonpath = os.path.commonpath
commonprefix = os.path.commonprefix


def dirname(path, make_assumptions = default_make_assumptions):
    """
    Overrides os.path.dirname
    :param path:
    :return:
    """
    return Path(path).folder_part(make_assumptions = make_assumptions)


parent = dirname

exists = os.path.exists
expanduser = os.path.expanduser
getatime = os.path.getatime
getmtime = os.path.getmtime
getctime = os.path.getctime
getsize = os.path.getsize
isabs = os.path.isabs


def is_file(path_str, make_assumptions = default_make_assumptions):
    return Path(path_str).is_file(make_assumptions = make_assumptions)


def is_dir(path_str, make_assumptions = default_make_assumptions):
    return Path(path_str).is_dir(make_assumptions = make_assumptions)


getcwd = os.getcwd  # getcwd(): Return a string representing the current working directory.
chdir = os.chdir  # chdir(path): Change the current working directory to path.
chmod = os.chmod  # os.chmod(path, mode, *, dir_fd=None, follow_symlinks=True)
# Change the mode of path to the numeric mode. mode may take
# one of the following values (as defined in the stat module)
# or bitwise ORed combinations of them: https://docs.python.org/3/library/os.html#os-file-dir
# chroot = os.chroot
islink = os.path.islink
ismount = os.path.ismount
join = os.path.join
link = os.link  # os.link(src, dst, *, src_dir_fd=None, dst_dir_fd=None, follow_symlinks=True):
#  Create a hard link pointing to src named dst.
listdir = os.listdir  # os.listdir(path='.'): Return a list containing the
# names of the entries in the directory given by path.
# mkdirs = os.mkdirs  # os.makedirs(name, mode=0o777, exist_ok=False)
#                     # Recursive directory creation function. Like mkdir(), but
#                     # makes all intermediate-level  directories needed to
#                     # contain the leaf directory.
#                     # https://docs.python.org/3/library/os.html#os.makedirs
name = os.path.basename
normcase = os.path.normcase
normpath = os.path.normpath
readlink = os.readlink  # os.readlink(path, *, dir_fd=None):
# Return a string representing the path to which the symbolic link points.
realpath = os.path.realpath
relpath = os.path.relpath
remove = os.remove
rename = os.rename  # os.rename(src, dst, *, src_dir_fd=None, dst_dir_fd=None):
# Rename the file or directory src to dst.
renames = os.renames  # os.renames(old, new): Recursive directory or file renaming function.
replace = os.replace  # os.replace(src, dst, *, src_dir_fd=None, dst_dir_fd=None):
# Rename the file or directory src to dst. If dst is a directory, OSError
# will be raised. If dst exists and is a file, it will be replaced silently
# if the user has permission. https://docs.python.org/3/library/os.html#os-file-dir
rmdir = os.rmdir  # os.rmdir(path, *, dir_fd=None):
# Remove (delete) the directory path if  exists and not empty.
removedirs = os.removedirs  # os.removedirs(name): Remove directories recursively until
# non-empty dir is reached. https://docs.python.org/3/library/os.html#os-file-dir
samefile = os.path.samefile
sameopenfile = os.path.sameopenfile
samestat = os.path.samestat
scandir = os.scandir  # os.scandir(path='.'): Return an iterator of os.DirEntry objects
# corresponding to the entries in the directory given by path.  Using
# scandir() instead of listdir() can significantly increase the performance
# of code that also needs file type or file attribute information, because
# os.DirEntry objects expose this information if the operating system
# provides it when scanning a directory. https://docs.python.org/3/library/os.html#os-file-dir
stat = os.stat  # os.stat(path, *, dir_fd=None, follow_symlinks=True): Get the status of a file or
# a file descriptor. returns stat_result object with proprties: st_mode, st_ino,
# st_dev, st_nlink, st_uid, st_gid, st_size, st_atime, st_mtime, st_ctime,
# st_atime_ns, st_mtime_ns, st_ctime_ns
# Example result:
# os.stat_result(st_mode=33188, st_ino=7876932, st_dev=234881026,
# st_nlink=1, st_uid=501, st_gid=501, st_size=264, st_atime=1297230295,
# st_mtime=1297230027, st_ctime=1297230027)
supports_follow_symlinks = os.supports_follow_symlinks
symlink = os.symlink  # os.symlink(src, dst, target_is_directory=False, *, dir_fd=None):
# Create a symbolic link pointing to src named dst.
truncate = os.truncate  # os.truncate(path, length): Truncate the file corresponding to path, so
# that it is at most length bytes in size.
unlink = os.unlink  # os.unlink(path, *, dir_fd=None): Remove (delete) the file path. This
# function is semantically identical to remove();
utime = os.utime  # os.utime(path, times=None, *, [ns, ]dir_fd=None, follow_symlinks=True):
# Set the access and modified times of the file specified by path.
walk = os.walk  # os.walk(top, topdown=True, onerror=None, followlinks=False)


# Generate the file names in a directory tree by walking the tree either top-down
# or bottom-up. For each directory in the tree rooted at directory top (including
# top itself), it yields a 3-tuple (dirpath, dirnames, filenames).
# https://docs.python.org/3/library/os.html#file-names-command-line-arguments-and-environment-variables
# fwalk = os.fwalk    #  os.fwalk(top='.', topdown=True, onerror=None, *, follow_symlinks=False, dir_fd=None)
#                     # This behaves exactly like walk(), except that it yields a 4-tuple (dirpath,
#                     # dirnames, filenames, dirfd), and it supports dir_fd.
#                     # https://docs.python.org/3/library/os.html#os.fwalk


def splitdrive(path, find_implied = default_find_implied):
    result = os.path.splitdrive(path)
    if result:
        return result
    else:
        return Path(path).drive(find_implied = find_implied)


def split(path, make_assumptions = default_make_assumptions):
    if not make_assumptions:
        return os.path.split(path)
    else:
        p = Path(path, make_assumptions = True)
        return p.folder_part(), p.filename_sans_folders()


splitext = os.path.splitext
supports_unicode_filenames = os.path.supports_unicode_filenames


# ##############################################################################
# functions that are wrappers of os.path
#
# TODO: consider re-writing the functions below taking advantage of the Path class
#       defined above.
#
# ##############################################################################


def is_valid_dir(path_name, as_bool: bool = True):
    """
    Validate a path_name for use as a directory.
    :param path_name: name of path to validate
    :param as_bool: True: return a boolean
                    False: return a named tuple ('valid','type_code', 'description', 'path')
    :return: True if (1) the path exists and is a folder or
                     (2) the path does not exist, but the parent path
                         exists and is a folder (indicating that the
                         path can be created as a new directory)
    """
    ResultTuple = namedtuple('ResultTuple',
                             ['valid', 'type_code', 'description', 'path'])
    result = [False] + list(path_type(path_name))
    if result[1] in [1, 2, 3]:
        result[0] = True
    if as_bool:
        return result[0]
    else:
        return ResultTuple(result[0], result[1], result[2], result[3])


def is_valid_filename(filename, as_bool: bool = True):
    """
    Can I use filename to save a file?
    :param filename: string name of file.  May be full or partial path
    :param as_bool: True: return a boolean
                    False: return a named tuple ('valid','type_code', 'description', 'path')
    :return:
            True:  if filename (1) is an existing file OR (2) does not exist
                   but does fall inside of a valid folder structure
            False: filename is (1) an existing folder OR (2) is an invalid path.
    """
    ResultTuple = namedtuple('ResultTuple',
                             ['valid', 'type_code', 'description', 'path'])
    result = [False] + list(path_type(filename))
    if result[1] in [0, 2, 3]:
        result[0] = True
    if as_bool:
        return result[0]
    else:
        return ResultTuple(result[0], result[1], result[2], result[3])


def path_type(path_name: str, **kwargs):
    """
    Attempts to determines if path_name is an existing file or folder.  If not,
    then determine if some root part of the path_name exists.
    :param path_name: str name of path to inspect
    :param kwargs: do NOT use kwargs.  kwargs is used internally for recursion.
    :return: namedtuple(type_code, description, path)
         3, ancestor folder of path_name levels up exits.path_name can be used for
            a new  folder or file.
         2, parent folder of path_name exists; path_name can be used for a new
             folder or file.
         1, path_name is an existing dir
         0, path_name is an existing file
        -1, path_name must be a non-zero length string
        -2, invalid path; must contain a valid root dir
             this indicates that path_name could
             be used for a new folder or file.
        -3, invalid path name; sub-folder name is an existing FILE

    """
    # Initialize
    # ##########################################################################
    ResultTuple = namedtuple('ResultTuple', ['type_code', 'description', 'path'])

    _level_ = 0
    if '_level_' in kwargs:
        _level_ = kwargs['_level_']

    # convert path_name to absolute path (don't need to do this if level > 0,
    # since we would have done so already on the first pass (level 0).
    if path_name and _level_ == 0:
        path_name = os.path.abspath(path_name)

    # Evaluate path_name
    # ##########################################################################
    if not path_name:
        # path_name is an empty str
        if _level_ == 0:
            # this is our first pass, an empty string was provided
            return ResultTuple(-1, TYPE_DICT[-1], path_name)
        else:
            # This is our last (and at least second) pass; in prior passes, we
            # found that ALL parts of the path do not exist.  So, this path
            # is invalid even at the root level.
            return ResultTuple(-2, TYPE_DICT[-2], path_name)
    elif os.path.exists(path_name):
        if os.path.isfile(path_name):
            if _level_ == 0:
                # the originally provided path_name exists and is a file
                return ResultTuple(0, TYPE_DICT[0], path_name)
            else:
                # invalid path name; sub-folder name is an existing FILE
                # example: folder/existing_file/folder, which is invalid
                return ResultTuple(-3, TYPE_DICT[-3],
                                   path_name)
        elif os.path.isdir(path_name):
            if _level_ == 0:
                # the originally provided path_name exists and is a folder
                return ResultTuple(1, TYPE_DICT[1], path_name)
            elif _level_ == 1:
                # parent dir "{path_name}" exists; path_name can be used for a new
                # folder or file.
                return ResultTuple(2, TYPE_DICT[2], path_name)
            elif os.path.exists(path_name):
                # ancestor folder {level} levels up exits.path_name can be used for
                # a new  folder or file.
                return ResultTuple(3, TYPE_DICT[3], path_name)
            elif _level_ < 100:
                return path_type(path_name = os.path.split(path_name)[0],
                                 _level_ = _level_ + 1)
            else:
                raise RecursionError('Unexpected error evaluating path_type("{path_name}")')
        else:
            # This is never expected.
            raise NotImplementedError
    elif path_name[1:] in [':\\', r':/', ':\\\\']:
        return ResultTuple(-2, TYPE_DICT[-2],
                           path_name)
    elif _level_ < 100:  # path does not exist
        return path_type(path_name = os.path.split(path_name)[0],
                         _level_ = _level_ + 1)
    else:
        raise RecursionError('Unexpected error evaluating path_type("{path_name}")')


def parse_path(filename: str):
    """
    Perform a basic filename validation.  This is a cursory check; it does not
    guarantee a valid filename.
    :param filename: (str) a filename to test
    :return: tuple of (pass, get_drive, folder, file, extension), where
        pass = True if filename is path-like, else False
    """
    # If the path exists, then we can assume it is valid.
    PathParts = namedtuple('PathParts', ['folder_exists', 'basename_exists', 'drive_folder',
                                         'get_drive', 'folder', 'basename', 'file', 'ext'])
    folder_exists = False
    basename_exists = False
    if os.path.exists(filename):
        abs_path = os.path.abspath(filename)
        if os.path.isdir(filename):
            fp_type = 'dir'
            drv_fldr, base = abs_path, ''
            drv, fldr = os.path.splitdrive(drv_fldr)
            f, ext = '', ''
            return PathParts(True, False, drv_fldr, drv, fldr, base, f, ext)
        elif os.path.isfile(filename):
            fp_type = 'file'
            drv_fldr, base = os.path.split(abs_path)
            drv, fldr = os.path.splitdrive(drv_fldr)
            f, ext = os.path.splitext(base)
            return PathParts(True, True, drv_fldr, drv, fldr, base, f, ext)
        else:
            raise NotImplementedError('Unexpected Error.')
    else:
        # Split path_str into dir, file (part between dir and extension), extension (variables: d,
        # f, e)
        abs_path = os.path.abspath(filename)
        # fldr, base = get_drive:/folder, file.ext
        drv_fldr, base = os.path.split(abs_path)
        # split fldr to get_drive, folder
        drv, fldr = os.path.splitdrive(drv_fldr)
        # split base to file, ext
        f, ext = os.path.splitext(base)
        # path parts
        parts = drv, fldr, f, ext

        if os.path.exists(drv_fldr):
            if os.path.isdir(drv_fldr):
                return PathParts(True, False, drv_fldr, drv, fldr, base, f, ext)
            else:
                raise NotImplementedError('Unexpected Error.')
        else:
            return PathParts(False, False, drv_fldr, drv, fldr, base, f, ext)


def mkdir2(new_path: Union[Path, str], mode = 0o777, parents = False, exist_ok = False):
    """
    Create a new directory of name specified by named new_path.

    :param new_path:
    :param mode:
    :param parents:
    :param exist_ok:
    :return:
    """
    assert (type(new_path in [Path, str]))
    if type(new_path) == PathType:
        return new_path.mkdir(mode = mode, parents = parents, exist_ok = exist_ok)
    else:
        # type(new_path) == str:
        return Path(new_path).mkdir(mode = mode, parents = parents, exist_ok = exist_ok)


def mkdir(new_path: str) -> tuple:
    """
    wrapper for os.path.mkdir.  Instead of an error, create if not exists.

    :param new_path: string representing the partial or absolute path.
    :return: tuple of (status code, reason):
            (-1, 'ERROR: new_path already exists but is a FILE, NOT a dir')
            (0, 'SUCCESS: created new path')
            (1, 'SUCCESS: dir already exists and is empty')
            (2, 'WARNING: dir already exists but is NOT EMPTY')
    """
    # TODO - the unit test for this function fails.  Address this.
    if not os.path.exists(new_path):
        # create new_path
        try:
            os.mkdir(new_path)
            return 0, 'SUCCESS: created new path'
        except FileNotFoundError as e:
            parent = os.path.split(new_path)[0]
            if parent:
                mkparent = mkdir(parent)
                if mkparent[0] == 0:
                    try:
                        os.mkdir(new_path)
                        return 0, 'SUCCESS: created new path'
                    except Exception as e:
                        return -1, str(e)
                else:
                    return mkparent
            else:
                return -1, 'ERROR making "{new_path}";  {str(e)}'
        except Exception as e:
            return -1, 'ERROR making "{new_path}";  {str(e)}'
    elif os.path.isdir(new_path):
        # new_path already exists
        # Checking if the list is empty or not
        if len(os.listdir(new_path)) == 0:
            # dir exists and is empty :)
            return 1, 'SUCCESS: dir already exists and is empty'
        else:
            return 2, 'WARNING: dir already exists but is NOT EMPTY'
    elif os.path.isfile(new_path):
        # new_path exists, but is a file_util, not a folder/directory.
        return -1, f'ERROR: new_path "{new_path}" already exists but is a FILE, NOT a dir'
    else:
        raise NotImplementedError(f'This case for mkdir("{new_path}") not yet coded.')


# ##########
def is_path_like(filename: Union[Path, str]):
    """
    Perform a basic filename validation.  This is a cursory check; it does not
    guarantee a valid filename.
    ** Note: used in toolbox.config.Config
    :param filename: (str) a filename to test
    :return: tuple of (pass, get_drive, folder, file, extension), where
        pass = True if filename is path-like, else False
    """
    # If the path exists, then we can assume it is valid.
    if isinstance(filename, Path):
        return True
    elif os.path.exists(filename):
        if os.path.isdir(filename):
            return False, f'Error: "{filename}" is a directory; missing ' \
                          'basename (file.ext).', None, None, None
        # if os.path.isfile():
        #     return True, f'Info: "{os.path.abspath(filename)}" is an existing file.'

    # TODO: leverage the Path class, like: p = Path(filename)

    # Split path_str into dir, file (part between dir and extension), extension (variables: d,
    # f, e)
    abs_path = os.path.abspath(filename)
    # fldr, base = get_drive:/folder, file.ext
    fldr, base = os.path.split(abs_path)
    # split fldr to get_drive, folder
    drv, fldr = os.path.splitdrive(fldr)
    # split base to file, ext
    f, ext = os.path.splitext(base)
    # path parts
    parts = drv, fldr, f, ext

    # validate each part of the path: dir, file and extension
    if len(fldr) == 0 or len(f) == 0:
        result = False, 'Error: "{path_str}" is not a valid path', None, None, None
    elif len(ext) == 0:
        result = True, drv, fldr, f, ext
    else:
        result = True, drv, fldr, f, ext

    # if not os.path.isdir(fldr):
    #     result = True, drv, fldr, f, ext

    return result


def mk_parent(path: Union[Path, str], mode = 0o777, parents = True, exist_ok = True):
    return Path(path).parent.mkdir(mode = mode, parents = parents, exist_ok = exist_ok)


def backup_file(orig_file):
    def timestamp_str(utc = True):
        f = dtdt.utcnow if utc else dtdt.now
        if utc:
            return f().isoformat()[:19].replace(".", "_").replace(":", "-")
        else:
            return f().isoformat()[:19].replace(".", "_").replace(":", "-")

    orig = Path(orig_file)
    if not orig.exists():
        pass
    elif not orig.is_file():
        raise FileNotFoundError(f'File System Object "ora_snippets_file" exists but is not a file.')
    else:
        bck = timestamp_str()
        bck = orig.with_name(orig.stem + "_" + bck + orig.suffix)
        shutil.copyfile(src = orig_file, dst = bck)


if __name__ == '__main__':
    pass
