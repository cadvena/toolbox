import unittest
from toolbox.error_handler import ErrorHandler


class CustomException(Exception):
    pass


class Example1(object):
    # Aways put these two lines at the top of a class which will have some methods which you want to have error handling
    error_handler = ErrorHandler()
    ignore_errors = error_handler.ignore_errors

    @error_handler.wrap(on_error_return=0)
    def times2(self, value_in):
        assert(type(value_in) in (int, float))
        return value_in*2


class Example2(object):
    # Aways put these two lines at the top of a class which will have some methods which you want to have error handling
    error_handler = ErrorHandler()
    ignore_errors = error_handler.ignore_errors

    # This __init__() is not required.  It lets you set ignore_errors
    # in __init__, so you can instantiate MyClass and set the value
    # of ignore_errors in a single line of code.
    def __init__(self, ignore_errors:bool = None):
        if ignore_errors is not None:
            assert(type(ignore_errors) == bool)
            self.ignore_errors = ignore_errors
        self.ignore_errors = ignore_errors

    @error_handler.wrap(on_error_return=0)
    def times2(self, value_in):
        assert(type(value_in) in (int, float))
        return value_in*2


class MyClass(object):

    # Aways put these two lines at the top of a class which will have some methods which you want to have error handling
    error_handler = ErrorHandler()
    ignore_errors = error_handler.ignore_errors

    @error_handler.wrap()
    def my_func(self):
        raise CustomException("testing")

    @error_handler.wrap(on_error_return=[])
    def my_func_list(self):
        raise CustomException("testing2")


class MyOtherClass(object):

    error_handler = ErrorHandler()
    ignore_errors = error_handler.ignore_errors

    # These two lines are optional.  They let you set ignore_errors
    # in __init__, so you can instantiate MyClass and set the value
    # of ignore_errors in a single line of code.
    def __init__(self, ignore_errors = False):
        self._ignore_errors = ignore_errors

    @error_handler.wrap()
    def my_func(self):
        raise CustomException("from MyOtherClass")

    @error_handler.wrap(on_error_return=[])
    def my_func_list(self):
        raise CustomException("testing2")


class Test(unittest.TestCase):

    def test_example1(self):
        ex1 = Example1()
        ex1.ignore_errors = True
        self.assertEqual(ex1.times2(3), 6)
        self.assertEqual(ex1.times2('abc'), 0)

        ex1.ignore_errors = False
        self.assertEqual(ex1.times2(3), 6)
        with self.assertRaises(AssertionError):
            ex1.times2 ('abc')

    def test_example2(self):
        z = Example2(ignore_errors = True)
        self.assertEqual(z.times2(3), 6)
        self.assertEqual(z.times2('abc'), 0)

        z = Example2(ignore_errors = False)
        self.assertEqual(z.times2(3), 6)
        with self.assertRaises(AssertionError):
            z.times2 ('abc')

    def test_ignore_errors(self):
        a = MyClass()
        a.ignore_errors = True
        self.assertFalse(a.my_func())

    def test_raises_error(self):
        a = MyClass()
        self.assertFalse(a.ignore_errors)
        with self.assertRaises(CustomException):
            a.my_func()

    def test_ignore_errors_altname(self):
        a = MyOtherClass()
        a.ignore_errors = True
        self.assertFalse(a.my_func())

    def test_raises_error_altname(self):
        a = MyOtherClass()
        self.assertFalse(a.ignore_errors)
        with self.assertRaises(CustomException):
            a.my_func()

    def test_ignore_errors_list(self):
        a = MyClass()
        a.ignore_errors = True
        self.assertFalse(a.my_func_list())

    def test_raises_error_list(self):
        a = MyClass()
        self.assertFalse(a.ignore_errors)
        with self.assertRaises(CustomException):
            a.my_func_list()

    def test_ignore_errors_altname_list(self):
        a = MyOtherClass()
        a.ignore_errors = True
        self.assertFalse(a.my_func_list())

    def test_raises_error_altname_list(self):
        a = MyOtherClass()
        self.assertFalse(a.ignore_errors)
        with self.assertRaises(CustomException):
            a.my_func_list()


if __name__ == '__main__':
    unittest.main()