#!/usr/bin/env python3
"""
midas_touch is a python module and executable script that updates the
modified timestamp of files in the specified folder, path_name.

Syntax if run as executable script:
midas_touch --folder_name folder/folder --recursive True/False --days 120
    -f / --folder_name: name of target folder upon which to execute midas_touch
                        default: current directory
    -r / --recursive (bool): include sub-folders
                        default: True
    -d / --days (int): only touch files with dates at least this many days old.
                        default: 120
"""

__author__ = "Chris Advena"
__version__ = "0.1.0"
__license__ = "MIT"

import os
import time
import logging
import argparse
# from pathlib.py import Path
# from pprint import pprint
# from toolbox import tb_cfg


def touch(root, file, num_days = 120):
    touched = False
    fn = os.path.join(root, file)
    mod_time = os.stat(fn).st_mtime
    # threshold_time is current time minus num_days
    # Note: there are 86400 secs / day.
    threshold_time = time.time() - (86400 * num_days)
    # print('threshold_time: ', time.ctime(threshold_time))

    new_mod_time = None
    err = True
    try:
        if mod_time < threshold_time:
            os.utime(fn)
            new_mod_time = mod_time = os.stat(fn).st_mtime
            touched = True
            err = False
    except Exception as e:
        err = True
        log_txt = '@ ' + time.ctime() + ', touch(' + root + ', ' + file + '). Error: ' + str(e)
        logging.log(logging.CRITICAL, log_txt)

    if not err:
        log_txt = '@ ' + time.ctime() + ', touch(' + root + ', ' + file + ') = ' + str(touched)
        log_txt += ': ' + time.ctime(mod_time)
        if new_mod_time:
            log_txt += ', ' +time.ctime(new_mod_time)
            logging.log(logging.DEBUG, log_txt)

    return touched


def midas_touch(folder_name = os.getcwd(),
                num_days = None,
                recurse = True,
                retries = 0):
    """
    Update timestamp of files in path_name if the file is more than num_days
    old.  If recurse = True, then run recursively in sub-folders.
    :param folder_name: root directory in which to run
    :param num_days:
    :param recurse: recursively run in sub folders
    :return:
    """

    result = []
    cnt = 0
    fldr = ''
    fldr_cnt = len(list(os.walk(folder_name)))
    log_txt = 'midas_touch() processing ' + str(fldr_cnt) + ' folders in ' + folder_name + '...'
    print(log_txt)
    logging.log(logging.INFO, log_txt)
    if recurse:
        for root, dirs, files in os.walk(folder_name):
            if not fldr == str(root):
                fldr = str(root)
                cnt += 1
                if cnt%1000 == 0:
                    log_txt = '    completed ' + str(cnt) + ' of ' + str(fldr_cnt) + \
                              ' folders in ' + folder_name
                    logging.log(logging.INFO, log_txt)
                    print(log_txt)
            for file in files:
                result.append((touch(root, file), root, file))
    else:
        for file in os.listdir(folder_name):
            result.append((touch(folder_name, file, num_days), folder_name, file))

    if retries > 0:
        # TODO: add retry logic
        raise NotImplementedError

    return tuple(result)


def main(args):
    result = midas_touch(folder_name = args.folder_name,
                num_days = args.days,
                recurse = args.recursive)

    # pprint('*'*28 + ' Not Touched ' + '*'*28)
    # pprint([x for x in result if not x[0]])
    # print('\n\n')
    # pprint('*'*30 + ' Touched Files ' + '*'*30)
    # pprint([x for x in result if x[0]])


if __name__ == '__main__':
    """ This is executed when run from the command line """
    # logging: https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
    logging.basicConfig(filename = 'midas_touch.log', level = logging.DEBUG)
    logging.basicConfig()

    parser = argparse.ArgumentParser(
            description = "Midas Touch python script"
            )

    # Required arguements:

    # Optional arguments:
    parser.add_argument('-f', "--folder_name", action="store",
                        default = os.getcwd(),
                        help="Folder upon which to run.")
    parser.add_argument("-d", "--days", action="store", type=int, default=120)
    parser.add_argument("-r", "--recursive", action="store", default=True)
    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    args = parser.parse_args()
    main(args)