#!/usr/bin/env python3

"""
Executable script to backup and mirror selected folders.

Syntax: sync config_file [output_file]

Config_file format is csv with 3 columns: operation, source_folder, target_folder

Valid values for operation: mirror, backup
"""

__author__ = "Chris Advena"
__version__ = "0.1.1.dev1"
__license__ = "MIT"

from dirsync import sync
import pandas as pd
import logging
#from os import path
from os import mkdir
import time
import argparse
from toolbox.pathlib import is_valid_dir
# from toolbox import tb_cfg,


LOG_FILE = 'sync.log'
LOG_LEVEL = logging.INFO


def backup(source_path, target_path):
    # for syncing one way
    # https://pypi.org/project/dirsync/
    sync(sourcedir=source_path, targetdir=target_path,
         action='sync')


def mirror(path1, path2):
    # https://pypi.org/project/dirsync/
    sync(sourcedir = path1, targetdir = path2,
         action = 'sync', twoway = True, create=True)


def arg_parse():
    # Get config_file from the 1st (and only) positional command line argument.
    parser = argparse.ArgumentParser(
            description = "Midas Touch python script"
            )

    s = 'Required poitional argument, config_file: \n' \
        '    the name of the csv file containing the folders to sync. \n' \
        'Column headers: "operation", "source_folder", "target_folder" \n' \
        'operation may be "backup" or "mirror"'
    parser.add_argument("config_file", action="store", help=s)

    s = 'Optional argument: the name of the file in which to report the result ' \
        'of the file sync process.  If not provided, no result file is created'
    parser.add_argument("-o", "--output_file", action = "store", type = int, default = '')

    args = parser.parse_args()

    # Process arguments from terminal
    if not args.output_file:
        time_str = time.strftime('&Y_%m_%d_%H%M', time.time())
        output_file = f'sync_output_{time_str}.csv'
    else:
        output_file = args.output_file

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    return args.config_file, output_file


def main(config_file, output_file):
    # Read config file
    config_df = pd.read_csv(config_file)

    # Create df for results
    result_df = pd.DataFrame(columns = ['success', 'operation', 'source',
                                        'target_folder', 'log message'])
    # Process each row from the config file.
    for i, row in enumerate(config_df.iterrows()):
        line_num = i + 1
        # Validate row
        op = row[1][0]
        op = op.strip().strip('"').strip().lower()
        src = row[1][1].strip().strip('"').strip()
        tgt = row[1][2].strip().strip('"').strip()

        success = False
        msg = None
        if not is_valid_dir(src):
            msg = f'Invalid path "{src}" in column "source_folder", ' \
                                                     'line {line_num}.'
            result_df.append([False, op, src, tgt, msg])
            result_df.to_csv(output_file)
        elif not is_valid_dir(tgt):
            # TODO: implement exception handling
            # try:
            mkdir(tgt)
            # except Exception as e:
            #     msg = f'Invalid path "{tgt}" in column "target_folder", ' \
            #                                              'line {line_num}.'

        # Attempt backup or mirror operation
        msg = f'{op}: "{src}" -> "{tgt}"'
        print('Starting', msg)
        if op == 'backup':
            backup(src, tgt)
            success = True
        elif op == 'mirror':
            mirror(src, tgt)
            success = True
        else:
            msg = f'Error: Invalid operation "{op}", line {line_num}. ' \
                  f'Acceptable values are "backup" and "mirror".'

        result_df.append([success, op, src, tgt, msg])

    # Save results to disk
    result_df.to_csv(output_file)
    print(f'sync script finished. See results file, "{output_file}".')


if __name__ == '__main__':
    """ This is executed when run from the command line """

    # logging: https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
    logging.basicConfig(filename = LOG_FILE, level = LOG_LEVEL)
    logging.basicConfig()

    try:
        config_file, output_file = arg_parse()
    except:
        config_file = 'sync_config.csv'
        output_file = 'sync_results.csv'

    main(config_file, output_file)
