import os
import unittest
from toolbox.file_util.file_regex import replace_in_file


class TestClass(unittest.TestCase):
    def setUp(self):
        print("\nCalling TestOSWrapper.setUp()...")


    def tearDown(self):
        print("\nCalling TestOSWrapper.tearDown()...")

    def test_replace_in_file(self):
        # version = re.findall(regex, open(f).read())[0]
        file_path = "file_util_regex_replace_in_file.txt"
        find_text = r"__version__\s*=\s*['\"](.*?)['\"]"
        replace_with = "__version__ = '0.0.2.dev3'"
        # calling the replace method
        replace_in_file (file_path = file_path, regex_string = find_text,
                         replace_with = replace_with)


if __name__ == '__main__':
    ### 2 - invoke the framework ###
    # invoke the unittest framework
    # unittest.main() will capture all fo the tests
    # and run them 1-by-1.
    unittest.main ()
