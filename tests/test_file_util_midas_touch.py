# 1 - Import unittest (find 2 under "if __name__ == '__main__'")
import unittest
from toolbox.file_util import hash as h
from time import sleep
import os


class TestHash(unittest.TestCase):
    def setUp(self):
        print('')
        print(r"Calling .setUp()...")
        # if os.path.exists(self.key_filename):
        #     os.remove(self.key_filename)

    def tearDown(self):
        print('')
        print(r"Calling .tearDown()...")

    def test_sha256_hash_and_has_match(self):
        pass
        # raise NotImplementedError


if __name__ == '__main__':
    ### 2 - invoke the framework ###
    # invoke the unittest framework
    # unittest.main() will capture all fo the tests
    # and run them 1-by-1.
    unittest.main()
