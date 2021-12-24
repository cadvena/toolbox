# Version number incremented and build timestamp set by
# toolbox.toolbox_build_tools.increment_version.
# DO NOT MODIFY THE ENXT TWO LINES.
__version__ = '2021.11.1'
__build_timestamp__ = '2021-11-19'
__ver__ = float('.'.join(__version__.split('.')[:2]))

# ##############################################################################
# Imports
# ##############################################################################
from warnings import warn
from os import environ, path
from typing import Union
from toolbox.appdirs import user_config_dir
from toolbox.config import Config
from os import remove

try:
    import PySimpleGUI as sg
except ModuleNotFoundError as e:
    # print ('Unable to import PySimpleGui.', e)
    warn(f'Unable to import PySimpleGui. {e}')
except ImportError as e:
    # print ('Unable to import PySimpleGui.', e)
    warn(f'Unable to import PySimpleGui. {e}')

try:
    from toolbox.pathlib import parse_path, mkdir
    from toolbox.pathlib import Path
except:
    from pathlib import Path
    from os import mkdir
    def parse_path(path_str):
        return Path(path_str).parts

try:
    from toolbox.pjm_init import pjm_defaults
except ModuleNotFoundError as e:
    # warn(f'Unable to import pjm_defaults from toolbox.pjm_init. {e}')
    pjm_defaults = None
except ImportError as e:
    # warn(f'Unable to import pjm_defaults from toolbox.pjm_init. {e}')
    pjm_defaults = None

try:
    from toolbox.swiss_army import *
except:
    warn(f'Unable to import from toolbox.swiss_army. {e}')

__version_info__ = parse_version_info(__version__)  # toolbox.swiss_army.parse_version_info
toolbox_module_dir = Path(__file__).parent.resolve()

# ##############################################################################
# toolbox config folder and filename
# ##############################################################################
_cfg_basename = 'toolbox.cfg'
_cfg_fldr = Path(user_config_dir(appname = 'toolbox', roaming = True))
_cfg_file = _cfg_fldr.joinpath(_cfg_basename)

# ##############################################################################
# default config data
# ##############################################################################
toolbox_module_dir = Path(__file__).parent.resolve()
_web_crawler_ini = pathlib.join(toolbox_module_dir, 'web_crawler.ini')

_cfg_defaults = {
            'DEFAULT_USERNAME': environ['username'],
            'ORACLE': {'DIALECT': 'oracle', 'DRIVER': 'cx_oracle'},
            'SG_THEME': 'Black',
            'ORACLE_DBS': {'MY': ['MYPRD', 'MYSTG', 'MYTST'],
                           'YOUR': ['YOURPRD', 'YOURSTG', 'YOURTST'],
                          },
            'DEFAULT_HOSTS': ['MYPRD', 'MYSTG', 'MYTST'],
            'WEB_APPS': {'Microsoft': {'OFFICE365': ' https://ofice.com',
                                       'AZURE': ' https://azure.microsoft.com'},
                         'Google': {'GMAIL': ' https://gmail.com'},
                        },
            'WEB_CRAWLER_INI': _web_crawler_ini
           }

# this was only for temp use.  Make sure it is not used by deleting.
del _web_crawler_ini

# ##############################################################################
# Load toolbox configuration
# ##############################################################################

def toolbox_config(config_file: Union[str, Path] = _cfg_file, replace=False):
    """
    toolbox_config manages the main configuration file, tb_cfg, used thorughout
    the toolbox library.  Generally, it contains default values.  However, it
    also contains useful metadata for PJM users, like a common list of database
    names, PJM CA proxies, etc.  If config_file is not found, this function will
    create one from scratch and store some default values.
    :param config_file: the filename or Path object representing the config file
    :param replace:  True: first delete the old config file.
                    False: use the existing config file if found
    :return: returns a toolbox.config.Config object (a dict based class)
    """
    # If config_file is not a toolbox.path.Path object, convert it to one.
    if type(config_file) != type(Path): config_file = Path(config_file)
    # If config_file's folder does not exist, create it.
    Path(config_file.parent).mkdir(parents = True, exist_ok = True)

    if replace:
        try:
            remove(_cfg_file)
        except FileNotFoundError:
            pass
        except Exception as e:
            warn(f'Unable to replace toolbox_config file, {_cfg_file}.  {e}')
    # Load/create and update toolbox_config from Config class, which inherits from dict.
    cfg = Config(file = _cfg_file, auto_save = False)
    # if pjm_init.py exists, get defaults from there
    if pjm_defaults:
        cfg.update_if_none(pjm_defaults)
    # after getting pjm specific config info, fill in any missing config info.
    cfg.update_if_none(_cfg_defaults)

    # SAVE changes to config.  Changes occur on (1) 1st import of
    # toolbox after installation and (2) 1st import of toolbox after a new
    # release containing new default config info.
    try:
        cfg.save()
    except IOError as e:
        print(f'unable to save changes to "{_cfg_file}". {e}')
    except Exception as e:
        raise

    cfg.auto_save = True
    return cfg

# load config
tb_cfg = toolbox_config()


if __name__ == '__main__':
    toolbox_config(_cfg_file, replace = True)
    if any (["sg" in s () for s in [globals, locals]]):
        sg.theme(tb_cfg['SG_THEME'])
    print('toolbox.__version_info__:', __version_info__)
    # print('default_config_basename:', _cfg_basename)
    print('toolbox_module_dir:', toolbox_module_dir)
    # print('default_config_file:', _cfg_file)
    # print('user_config_folder:', _cfg_fldr)
    print('toolbox config file (tb_cfg._file):', tb_cfg._file)