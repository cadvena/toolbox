from toolbox import appdirs
from toolbox.config import Config
from toolbox.pathlib import Path
from toolbox import path
import os

default_config_dir = appdirs.user_config_dir(appname= 'cleanup_folders')
path.mkdir(default_config_dir)
default_cfg_file = path.join(default_config_dir, 'cleanup_folders.config')

def default_config(cfg_file = default_cfg_file):
    path.mk_parent(cfg_file)
    Path(cfg_file).parent.mkdir(parents = True, exist_ok = True)
    # d = dict of {folder: expire_in_days}
    d = {'C:/temp': 120,
         'C:/Users/advena/Downloads/ScreenCaptures': 120,
        }
    cfg = Config (filename = cfg_file, auto_save = True, roaming = True)