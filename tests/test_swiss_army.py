# -- 1 -- Import unittest (find 2 under "if __name__ == '__main__'")
# import unittest is required
import unittest
# import the module being tested
# from toolbox.toolbox import swiss_army as sa
from toolbox import swiss_army as sa
# other imports
import os
import pandas as pd
import numpy as np


# -- 3 -- Write 'Test...' class and 'test_...' methods.
# Begin test classes with "Test"
class TestSwissArmy(unittest.TestCase):
    def setUp(self):
        print(r"Calling .setUp()")

    def tearDown(self):
        print(r"Calling .tearDown()")

    # -- 3.1 -- test cases
    # begin test methods with "test_"

    def test_is_iterable(self):
        self.assertTrue(sa.is_iterable('abc'), 'a string is iterable')
        self.assertTrue(sa.is_iterable([1,2,3]), 'a string is iterable')
        self.assertTrue(sa.is_iterable({1:1.1, 2:2.2, 3:3.3}), 'a dict is iterable')
        self.assertTrue(sa.is_iterable(pd.DataFrame()), 'a Pandas DataFrame is iterable')
        self.assertTrue(sa.is_iterable({1,2,3,4,5}), 'a set is iterable')
        self.assertFalse(sa.is_iterable(1.5), 'a float is not iterable')
        self.assertFalse(sa.is_iterable(os), 'built-in class "os" is not iterable')

    def test_make_iterable(self):
        def make_iterable_wrapper(anything, return_type = list,
                  string_is_iterable: bool = True,
                  *args, **kwargs):
            try:
                return sa.make_iterable(anything, return_type,
                                        string_is_iterable)
            except NotImplementedError:
                return 'NotImplementedError'

        def some_func():
            return False

        # things = (sa.is_iterable, os, 0.0, 0, 'a, b, c, d', None, '')
        # return_types = (list, tuple, set, pd.DataFrame, np.array, sa.is_iterable,
        #                 'space separated string', 'comma, separated, string')
        num_tbl = [[1,2,3],[4,5,6],[7,8,9]]
        """
        inputs: list of innner lists, where inner list is like 
        [thing, return_type, string_is_iterable, expected_result] 
        """
        inputs = [
                [some_func, list, True, 'NotImplementedError'],
                [os, tuple, False, 'NotImplementedError'],
                [0.0, list, True, [0.0]],
                [0, tuple, False, [0]],
                ['a, b, c, d', tuple, True, 'a, b, c, d'],
                [None, list, True, []],
                ['space separated string1', tuple, True, 'space separated string1'],
                ['space separated string2', tuple, False, ('space', 'separated', 'string2')],
                ['comma, separated, string1', tuple, True, 'comma, separated, string1'],
                ['comma, separated, string2', tuple, False, ('comma', 'separated', 'string2')],
                # [num_tbl, pd.DataFrame, False, pd.DataFrame(num_tbl)],
                # [num_tbl, np.array, False, np.array (num_tbl)]
            ]

        for row in inputs:
            res = make_iterable_wrapper(anything = row[0], return_type = row[1],
                                        string_is_iterable = row[2])
            msg = f'"{str(row[:-1])}" returned "{str(res)}", ' \
                  + f'expected "{str(row[-1])}"'
            self.assertEqual(res, row[3], msg)

    def test_is_valid_url(self):
        # Test cases: pairs of [url, valid], where
        #   url is a string to test
        #   valid is True if url is a good url, else False

        #         url,                   valid
        url_valid_pairs = [['https://www.pjm.com', True],
                ['https://pjm.com', True],
                ['https://.www.pjm.com', False],
                ['http://www.pjm.com', True],
                ['http://pjm.com', True],
                ['http://pjm', False],
                ['ftp', False],
                ['ftp://ftp', False],
                ['ftps://ftp.pjm.com', True],
                ['ftp://ftp.pjm.com/oasis', True],
                ['ftps://ftp.pjm.com/oasis/', True],
                ['ftp://ftp.pjm.com/oasis/file.ext', True],
                ]
        # loop through each pair of url_valid_pairs to see if is_valid_url()
        # returns the expected result (bool).
        for url, valid in url_valid_pairs:
            self.assertEqual(valid, sa.is_valid_url(url))


if __name__ == '__main__':
    # -- 2 -- invoke the framework --
    # invoke the unittest framework
    # unittest.main() will capture all fo the tests
    # and run them 1-by-1.
    unittest.main()
