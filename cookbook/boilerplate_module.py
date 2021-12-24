#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "Chris Advena"
__version__ = "0.1.0"
__license__ = "MIT"

from os import path
import argparse
try:
    from logzero import logger
except:
    class Logger:
        def __init__(self, log_file = None):
            self.log_file = log_file
            if not log_file: self.log_file = path.basename(path.splitext(__file__)[0]) + '.log'
            self.fmt = '%Y/%m/%d %H:%M:%S'

        def now_str(self):
            return dtdt.now().strftime(self.fmt)
        def log(self, *args, level = 'I'):
            with open(self.log_file, mode = "a") as file:
                for arg in args:
                    line = '[' + level + ' ' + dtdt.now().strftime(self.fmt) + ']  ' + str(arg)
                    file.write(line)
                    print(line)
        info = log
        warn = log
    logger = Logger()


# If module will never be run as script from terminal (command line), then you can
# delete (1) the "import argparse" line and the entire "def read_args():" function definition.
# References:
#   https://docs.python.org/3/library/argparse.html#module-argparse
#   https://www.python-boilerplate.com/py3+executable+argparse
def read_args(return_dict = False):
    parser = argparse.ArgumentParser()

    # # Required positional argument
    # parser.add_argument(""arg", help="Required positional argument")

    # Optional argument flag which defaults to False
    # parser.add_argument("-f", "--flag", action="store_true", default=False)

    # # Optional argument which requires a parameter (eg. -d test)
    parser.add_argument("-n", "--name", action="store", dest="name", default='boilerplate_module')

    # # Optional verbosity counter (eg. -v, -vv, -vvv, etc.)
    # parser.add_argument(
    #     "-v",
    #     "--verbose",
    #     action="count",
    #     default=0,
    #     help="Verbosity (-v, -vv, etc)")

    # # Specify output of "--version"
    # parser.add_argument(
    #     "--version",
    #     action="version",
    #     version="%(prog)s (version {version})".format(version=__version__))

    # Parse the arguments to variable named 'args' of type Namespace.
    # https://docs.python.org/3/library/argparse.html#the-namespace-object
    args =  parser.parse_args()

    # optionally return a python dict instead of a Namespace object.
    if return_dict: args = vars(args)
    return args

# Do not delete main()
def main():
    """ Main entry point of the app """
    # logger.info("Logging for {__name__}.main()")

    # If module will never be run as script from terminal (command line), then you can
    # delete this block of code.
	# Check to see if read_args() function exists (defined above).  If so, read the command-line args.
    if any (["read_args" in s () for s in [globals, locals]]):
		# Double-check that read_args is a callable function.
        if callable (read_args):
            # 1. Pick method 1, 2 or 3; delete the methods you don't use.
            # 2. Customize the method for your specific command-line args.
			
            # Method 1: args as dict
            args = read_args(return_dict = True)
            # logger.info(args)
            print('command line args returned as dict.')
            for k, v in args.items():
                print(k + ":", v)
        
            # Method 2: args as Namespace 
            args = read_args(return_dict = False)
            # logger.info(args)
            print('command line args returned as Namespace.')
            print('args.name: ', args.name)

            # Method 3: read a single commandline arg directly to a variable
            name_str = read_args().name
            print('name_str: ', name_str)
            # logger.info(name_str)


    else:
	    args = []

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()