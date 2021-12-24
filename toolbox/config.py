#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from typing import Union
import os
from warnings import warn
# from toolbox.file_util.path import is_valid_dir
from toolbox.appdirs import user_config_dir
from toolbox import path
try:
    from toolbox.pathlib import Path
except Exception as e:
    from pathlib import Path
    warn(f'Error in toolbox.config.  Unable to import Path from toolbox.path.  '
         f'Imported Path from pathlib instead.  {e}')
# import typing

# If set to true, then every time a category or parameter is set, Config will
# save the entire Config.config (dict of dicts) to file.
AUTO_SAVE: bool = True

"""
Config class is an extension of the built-in dict class.  Config is essentially a 
dict class with save/read capability.  A great feature is auto_save, which 
automatically saves every update to disk.  If you find, this impacts performance, set
auto_save = False and manually call the .save() method.



# You can use all of tme methods available in a dict, like:
#    setdefault, update,  keys, items, values, fromkeys, pop, popitem
# You can also use these added methods:
    save: save the config to disk
    load: load the config from disk
    exists: see if a parameter (i.e., a key) exists
    parameters: alias for .keys()
    update_if_none: appends the key/value pair is the key does not already exist.  
                    Returns a dict containing only key/value paris that were updated./
    copy: returns a copy of the Config object.
# THe following properties are also available:
#   filename: str = the name of the file in which to save the dictionary of config info
#   auto_save: bool = True: save every change in real-time, False
"""


def example_config_file_from_filename():
    # Let's set some default values in case a config file does not yet exist.
    DEFAULT_CONFIG = {'user': None, 'database': 'exscrprd',
                      'dir_out': r'C:/Personal/Workspace'}

    # Initialize a configuration object.  If the config file exists, it is
    # loaded, if not, it is created.
    cfg_fldr = Path (user_config_dir (appname = "example_config", roaming = True))
    cfg_fldr.mkdir()
    cfg_file = cfg_fldr.joinpath('example1.config')
    # cfg_file = os.path.join(user_config_dir(appname = "example_config", roaming = True), 'example1.config')
    cfg = Config(file = cfg_file, auto_save = True, roaming = True)

    # By default auto_save = True, so all of your changes are saved to your
    # config file.  So you never have to issue a load or save command, unless
    # you want to.
    print('\ncfg.auto_save:', cfg.auto_save)

    # If the config file did not exist or if any of config parameters from
    # DEFAULT_CONFIG are not in the config file, set the values.  If any
    # of the config parameters already exist, those parameters will NOT be overwritten.
    cfg.update_if_none(DEFAULT_CONFIG)

    # Overwrite values from cfg
    cfg['user'] = 'blue'
    # or
    cfg.set('user', os.environ['username'])

    # use cfg just like a dict object
    print('user:', cfg['user'])

    # where did we save cfg?
    print('config file:', cfg._file)

    # ignore the next line.  it is used in the unittest script
    return cfg_file


def example_config_file_from_appname():
    DEFAULT_CONFIG = {
        'user': None, 'database': 'exscrprd',
        'dir_out': r'C:/Personal/Workspace'
    }
    cfg = Config (appname = 'fake_app', auto_save = True,
                  roaming = True, dict_in = DEFAULT_CONFIG)
    print (cfg)
    print ()
    print ('config file name:', cfg._file)


def dict_recursive_update_if_none(existing_dict: dict, new_dict: dict):
    """
    Recursively add values from new_dict to existing_dict.  Only add new values;
    do not update existing entries.
    - New key:value pairs (key not already in existing_dict)
        - Add new key:value pair to dict.
    - Updated values (key already in existing_dict)
        - If the values in new_dict and existing_dict are both dicts
          (values don't have to be the same), then recursively run this func on
          those sub-dicts.
        - Else don't updated existing_dict, since a value already exists.
    :param existing_dict: existing dict to be updated
    :param new_dict: new values to enter if an existing value does not already exist.
    :return: udpated dict
    """
    for key, val in new_dict.items():
        if key not in existing_dict:
            # add new key/value pair
            # existing_dict.setdefault(key,val)
            existing_dict[key] = val
        elif isinstance(existing_dict[key], dict) and isinstance(val, dict):
                # key is a dict in both existing and new dicts.  Recurse.
                existing_dict[key] = dict_recursive_update_if_none(existing_dict[key], val)
    return existing_dict


def dict_recursive_update(existing_dict: dict, new_dict: dict):
    """
    Recursively add values from new_dict to existing_dict.
    :param existing_dict: existing dict to be updated
    :param new_dict: new values to enter if an existing value does not already exist.
    :return: udpated dict
    """
    for key, val in new_dict.items():
        if isinstance(val, dict) and key in existing_dict and isinstance(existing_dict[key], dict):
            existing_dict[key] = dict_recursive_update(existing_dict[key], val)
        else:
            existing_dict[key] = val
    return existing_dict


class Config(dict):
    """
    Configuration data manager with data stored/retrieved in a simple Python Dictionary.
    """
    def __init__(self, file: Union[Path, str, None] = None,
                 appname = None,
                 appauthor = None,
                 appversion = None,
                 roaming = True,
                 auto_save: bool = AUTO_SAVE,
                 dict_in: dict=dict(),
                 recursive_updates = True):
        """
        Initialize Config.
        :param file: - deprecated in version 2021.8.4.  It remains for bakcward
        compatibility.  Use of appname is prefered.
        :param appname: the name of the application.  this is used in determining
                        the auto-generated config file name.  See the appdirs.py
                        module for more information.
        :param appauthor: the name of the application.  this is used in determining
                        the auto-generated config file name.  See the appdirs.py
                        module for more information.
        :param appversion: the name of the application.  this is used in determining
                        the auto-generated config file name.  See the appdirs.py
                        module for more information.
        :param roaming: the name of the application.  this is used in determining
                        the auto-generated config file name.  See the appdirs.py
                        module for more information.
        :param auto_save: True/False.  If True, every change to Config is
                        automatically saved to disk.
        :param dict_in: Optionally, provide a dict of config data to be
                        imported/updated into Config
        """
        super().__init__()
        self.auto_save = auto_save
        self.recursive_updates = recursive_updates
        if file and appname:
            raise SyntaxError('Config expects appname or filename, not both')
        elif file:
            if not isinstance(file, Path): file = Path(file)
            if not file.parent_exists(): file.parent.mkdir(parents = True, exist_ok = True)
            self._file = file
        elif appname:
            user_dir = user_config_dir(appname = appname, appauthor = appauthor,
                              version = appversion, roaming = roaming)
            self._file = Path(os.path.join(user_dir, str(appname) + '.config'))
        else:
            raise SystemError('Config requires filename or appname.')
        if len(dict_in) > 0:
            if os.path.exists(self._file):
                if os.path.isfile(self._file):
                    self.load
            self.update(dict_in)
            if self.auto_save:
                self.to_json()
        else:
            self.load()

    def clear(self):
        """
        Remove all config data.  Filename and autosave settings remain.
        !!! Danger !!!  If you run self..clear() and self.auto_save == True,
        then you will also erase the config data from the config file!
        If you don't want to erase the config file, try self.whipe() instead.
        """
        result = super().clear()
        if self.auto_save:  # this should be taken care of by __setitem__
            self.to_json()
        return result

    @property
    def file(self) -> Path:
        """
        :return: toolbox.path.Path object of the configuration file.
        """
        if isinstance(self._file, Path):
            return self._file
        else:
            return Path(self._file)

    @property
    def path(self) -> Path:
        """
        alias of Config.file property
        :return: toolbox.path.Path object of the configuration file.
        """
        return self.file

    @property
    def filename(self) -> str:
        return str(self._file)

    @file.setter
    def file(self, new_file: Union[Path, str]):
        """
        Set the name of the file in which to save the configuration data.
        :param new_file: the name of the configuration file
        """

        if not isinstance(new_file, Path): new_file = Path(new_file)
        # if new_filename has no extension, append '.config'
        if len(new_file.suffixes) == 0:
            new_file = new_file.with_suffix('.config')
        # check that new_filename looks like a path
        path_like = path.is_path_like(new_file)
        if not path_like:
            raise ValueError(path_like)

        self._file = new_file

        if self.auto_save and len(self.keys()) > 0:
            self.to_json()

    @property
    def abs_path(self):
        return Path(self.filename).absolute()

    @property
    def folder(self):
        return Path(self.filename).folder_part()

    @property
    def folder_name(self):
        return str(self.folder)

    @staticmethod
    def is_path_like(filename:str):
        """
        Perform a basic filename validation.  This is a cursory check; it does not
        guarantee a valid filename.
        :param filename: (str) a filename to test
        :return: tuple of (pass, drive, folder, file, extension), where
            pass = True if filename is path-like, else False
        """
        return path.is_path_like(filename = filename)

    def read_json(self):
        """ Load configuration data from file. """
        # load configuration data from json file
        # if os.path.exists(self._file):
        if self._file.exists():
            with open(self._file, 'r') as json_file:
                d = json.load(json_file)
                super().__init__(d)
    load = read_json

    def to_json(self):
        """ Write dictionary of dictionaries to config file. """
        # convert self.dict (a dictionary) to json string, then encode to binary string.
        json_bin = json.dumps(self.dict, indent = 4).encode()
        self._file.parent.mkdir(parents = True, exist_ok = True)
        # drive_folder = self._file.drive_folder()
        # drive_folder = parse_path(self._filename).drive_folder
        # made_dir = mkdir(drive_folder)
        # if made_dir[0] >= 0:
        with open(file = self.filename, mode = 'wb') as json_file:
            json_file.write(json_bin)
        # else:
        #     raise FileNotFoundError(f'ERROR in Config.to_json({self._filename}).  {made_dir[1]}')
        del json_bin
    save = to_json

    @property
    def dict(self):
        """
        At times, it may be beneficial to get the dict object containing the configuration data
        instead of the full Config object.  This method does just that.
        :return: dict of parameter / parameter_value pairs.
        """
        return dict(super().items())
        # return super().__dict__

    @dict.setter
    def dict(self, *args, **kw):
        """
        TOTO: verify: Does not delete the old dict entries.  Adds/updates new entries.
        :param args:
        :param kw:
        :return:
        """
        super().__init__(*args, **kw)
        if self.auto_save:
            self.to_json()

    def pop(self, parameter_name, default = None):
        """
        Performs a python dictionary pop, which means it reads the value of the
        specified parameter_name (dict.key) and then removes the key/value pair.
        You can use the 'default' parameter to provide a value to return in the
        event that parameter_name does not exist.
        :param parameter_name: name of parameter to pop
        :param default: if parameter does not exist, use this value
        :return: value of parameter_name if it exists, else return value of default.
        """
        if default is None:
            result = super().pop(parameter_name)
        else:
            result = super().pop(parameter_name, default)
        # if self.auto_save:  # this should be taken care of by __setitem__
        #     self.to_json()
        return result

    def popitem(self):
        """
        Performs a dict.popitem() action on the config dict.
        :return: value of the popped item.
        """
        result = super().popitem()
        # if self.auto_save:  # this should be taken care of by __setitem__
        #     self.to_json()
        return result

    def exists(self, parameter_name: str) -> bool:
        """
        Determine is parameter_name exits.
        :param parameter_name:
        :return: True if parameter_name exists, else False.
        """
        # return parameter_name in self.keys()
        return self.__contains__(parameter_name)

    # exists = super().__contains__

    @property
    def parameters(self, *args):
        """
        Get the parameter names (not values).  Equivalent to dict.keys()
        :return: parameter names
        """
        return self.keys(*args)

    def __delitem__(self, v):
        """Ensure we launch auto-save after deleting a dict item."""
        result = super().__delitem__(v)
        if self.auto_save:
            self.to_json()
        return result

    def __setitem__(self, parameter, parameter_value):
        """Ensure we launch auto-save after setting a dict item."""
        result = super().__setitem__(parameter, parameter_value)
        if self.auto_save:
            self.to_json()
        return result

    def set(self, parameter_name: str, parameter_value):
        """Equivalent to:
            Config[parameter] = value
            if self.auto_save: sefl.save()
        """
        result = super().update({parameter_name: parameter_value})
        # if self.auto_save:
        #     self.to_json()
        return result

    def update(self, dict_of_parameters: dict, recurse = None):
        """
        Ensure we launch auto-save after setting a updating item.
        Equivalent to:
            super.update(dict_of_parameters)
            if self.auto_save: self.to_json()
        """
        # add/update key/value pairs
        if recurse is None:
            recurse = self.recursive_updates

        if recurse:
            self.dict = dict_recursive_update(self.dict, dict_of_parameters)
        else:  # recurse == False
            return super().update(dict_of_parameters)

        # if self.auto_save:  # this should be taken care of by __setitem__
        #     self.to_json()
    set_multi = update

    def update_if_none(self, dict_of_parameters: dict, recurse = None):
        """
        If any parameter in new_parameters_dict does NOT already exist, then
        append the parameter/value pair (key/value pair).
        """
        if recurse is None:
            recurse = self.recursive_updates

        if recurse:
            self.dict = dict_recursive_update_if_none(self.dict, dict_of_parameters)
        else:
            super_keys = list(super().keys())
            d = {p: v for (p, v) in dict_of_parameters.items() if p not in super_keys}
            return super().update(d)

        # super ().__init__ (d)
        # if self.auto_save:  # this should be taken care of by __setitem__
        #     self.to_json()

    update_default = update_if_none

    def setdefault(self, parameter_name: str, parameter_value):
        """Ensure we launch auto-save after 'setdefault' of dict.item()"""
        result = super().setdefault(parameter_name, parameter_value)
        # if self.auto_save:  # this should be taken care of by __setitem__
        #     self.to_json()
        return result

    def copy(self, file: Union[Path, str]):
        """
        Return a new Config object that is a copy of the current instance.
        """
        return Config(file = file,
                      auto_save = self.auto_save,
                      dict_in = self.dict.copy())

    def __eq__(self, other):
        """
        Compare equality of two Config objects.
        :param other:
        :return: True if both Config.dict objects are equal.
        """
        if isinstance(other, Config):
            return self.dict == other.dict
            # return self._file == other.filename \
            #     and self.auto_save == other.auto_save \
            #     and self.dict == other.dict:
        else:
            return self.dict == other


if __name__ == '__main__':
    example_config_file_from_filename()
    example_config_file_from_appname()
