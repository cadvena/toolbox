import unittest


class TestClass(unittest.TestCase):
    def setUp(self):
        print("\nCalling TestOSWrapper.setUp()...")


    def tearDown(self):
        print("\nCalling TestOSWrapper.tearDown()...")

    def test_something(self):
        pass

    if __name__ == '__main__':
        ### 2 - invoke the framework ###
        # invoke the unittest framework
        # unittest.main() will capture all fo the tests
        # and run them 1-by-1.
        unittest.main ()
