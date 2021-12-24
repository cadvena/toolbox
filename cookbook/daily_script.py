#!/usr/bin/env python3
"""
Chris Advena's daily script to touch (update modified timestamp) and backup (i.e., sync or mirror) files.

Requires midas_touch and sync modules by Chris Advena
Requires a daily_script_config.py file.
Requires dirsync package (pip install dirsync)

To customize the script, modify the constants (RUN_MIDAS_TOUCH, RUN_SYNC,
LOG_FILE, TOUCH_FOLDERS, SYNC_FOLDERS, PRINT_LOG_TO_CONSOLE) to customize.
"""

__author__ = "Chris Advena"
__version__ = "0.1.0"
__license__ = "MIT"

from toolbox.config import Config
import os
from toolbox.file_util.midas_touch import midas_touch
from toolbox.log_util import log_trimmer
# from toolbox import tb_cfg
import logging
import dirsync  # https://pypi.org/project/dirsync/
import time
from toolbox.keep_awake import keep_awake


LOG_AS_LEVEL = logging.INFO
HOME_DIR = os.getcwd()
DEFAULT_CONFIG_FILE = os.path.join(HOME_DIR, 'daily_script.cfg')

# Let's set some default values in case a config file does nto yet exist.
DEFAULT_TOUCH_FOLDERS = [r'C:\Personal',
                         r'F:\Personal',
                         r'C:\Projects',
                         r'\\corp.pjm.com\shares\TransmissionServices',
                         r'\\corp.pjm.com\shares\ATC',
                        ]
DEFAULT_CONFIG = {'MAX_LOG_SIZE': 50000000,
                  'LOG_TRIM_RATIO': 0.9,
                  'RUN_MIDAS_TOUCH': False, 'NUM_DAYS': 120,
                  'TOUCH_FOLDERS': DEFAULT_TOUCH_FOLDERS,
                  'RUN_SYNC': True,
                  'SYNC_FOLDERS': [['backup',
                                    r'C:\Users\advena\AppData\Roaming',
                                    r'D:\Backup\Users\advena\AppData']
                                   ],
                  'LOG_FILE':r'daily_script.log',
                  'PRINT_LOG_TO_CONSOLE':True
                 }


def get_config(cfg_file = DEFAULT_CONFIG_FILE):
    # Initialize a configuration object.  If the config file exists, it is
    # loaded, if not, it is created.
    cfg = Config(file = cfg_file, auto_save = True)

    # If the config file did not exist or if any of config parameters from
    # DEFAULT_CONFIG are not in the config file, set the values.  If any
    # of the config parameters already exist, thos parameters will NOT be overwritten.
    cfg.update_if_none(DEFAULT_CONFIG)

    return cfg


@keep_awake
def main():
    """ Main entry point of the app """

    # logging: https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
    cfg = get_config(cfg_file = DEFAULT_CONFIG_FILE)

    def log(log_txt,
            level = LOG_AS_LEVEL,
            print_to_console =
            cfg['PRINT_LOG_TO_CONSOLE']):
        logging.log(level = level, msg = log_txt)
        if print_to_console:
            print(log_txt)

    log_trimmer(cfg['LOG_FILE'], max_log_size = cfg['MAX_LOG_SIZE'], trim_ratio =
    cfg['LOG_TRIM_RATIO'])

    logging.basicConfig(filename = cfg['LOG_FILE'], level = LOG_AS_LEVEL)
    logging.basicConfig()

    start = time.time()
    log('\n\n' + '*'*80)
    log('Starting script: ' + __file__)
    log(time.ctime(start))
    log('*'*80 + '\n\n')

    # SYNC
    if cfg['RUN_SYNC']:
        for row in cfg['SYNC_FOLDERS']:
            log_txt = 'Starting ' + row[0] + ': ' + row[1] + ' ' + row[2]
            log(log_txt)
            if row[0] == 'backup':
                dirsync.sync(sourcedir = row[1], targetdir = row[2],
                             action = 'sync', twoway = False, create = True)
            elif row[0] == 'mirror':
                dirsync.sync(sourcedir = row[1], targetdir = row[2],
                             action = 'sync', twoway = True, create = True)
            else:
                msg = 'Invalid operation "' + row[0] + '". ' \
                      'Acceptable values are "backup" and "mirror".'
                log(msg, level=logging.WARNING)

    # MIDAS TOUCH
    if cfg['RUN_MIDAS_TOUCH']:
        touch_list = []
        failed_list = []
        for fldr in cfg['TOUCH_FOLDERS']:
            log('Starting midas_touch for: ' + fldr)
            temp = midas_touch(fldr)
            touch_list.append(temp)
            # pass_list = [row for row in attempt1 if row[0]]
            failed_list.append([row for row in temp if not row[0]])

    stop = time.time()
    log('\n\n' + '*'*80)
    # log(f'Finished {__name__}: {__file__}')
    log('Finished ' + __file__)
    log('    at ' + time.ctime(stop))
    log('    run time: ' + time.ctime(stop - start))
    log('*'*80 + '\n\n')


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()

