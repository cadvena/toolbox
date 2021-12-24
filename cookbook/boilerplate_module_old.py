#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "Your Name"
__version__ = "0.1.0"
__license__ = "MIT"


# from logzero import logger

# If module will never be run as script from terminal (command line), then you can
# delete (1) the "import argparse" line and the entire "def read_args():" function definition.
# References:
#   https://docs.python.org/3/library/argparse.html#module-argparse
#   https://www.python-boilerplate.com/py3+executable+argparse
import argparse
def read_args(return_dict = False):
    parser = argparse.ArgumentParser()

    # # Required positional argument
    # parser.add_argument(""arg", help="Required positional argument")

    # Optional argument flag which defaults to False
    # parser.add_argument("-f", "--flag", action="store_true", default=False)

    # # Optional argument which requires a parameter (eg. -d test)
    parser.add_argument("-n", "--name", action="store", dest="name")

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
    args = []
    if any (["read_args" in s () for s in [globals, locals]]):
        if callable (read_args):
            args = read_args()
        # logger.info (args)
	print(args)
	if "name" in args:
		print(args.name)


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()