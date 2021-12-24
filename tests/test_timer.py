# 1 - Import unittest (find 2 under "if __name__ == '__main__'")
import unittest
from toolbox import timer
from time import sleep


class TestTimer(unittest.TestCase):
    def setUp(self):
        print('')
        print(r"Calling .setUp()...")
        # if os.path.exists(self.key_filename):
        #     os.remove(self.key_filename)

    def tearDown(self):
        print('')
        print(r"Calling .tearDown()...")

    def test_start_stop(self):
        # create timer
        tmr = timer.Timer()
        # timer should be an empty list
        self.assertTrue(tmr.times == None)
        # start
        tmr.start()
        self.assertTrue(len(tmr.times) == 1)
        # pause
        sleep(2)
        # stop
        tmr.stop()
        self.assertTrue(len(tmr.times) == 2)


if __name__ == '__main__':
    ### 2 - invoke the framework ###
    # invoke the unittest framework
    # unittest.main() will capture all fo the tests
    # and run them 1-by-1.
    unittest.main()
