__author__ = 'Jason Sexauer'
__version__ = '2021.09.1'  # format: yyyy-mm-release_number
__version_info__ = __version__.split('.')

from collections import defaultdict

class ErrorHandler(object):
    """
    If you want to optionally ignore exceptions for some methods inside of a
    class, then use this class as a wrapper (decorator)

    * Example 1
    ****************************************************************************
    class Example1(object):
        # Aways put these two lines at the top of a class which will have some methods which you want to have error handling
        error_handler = ErrorHandler()
        ignore_errors = error_handler.ignore_errors

        @error_handler.wrap(on_error_return=0)
        def times2(self, value_in):
            assert(type(value_in) in (int, float))
            return value_in*2

    ex1 = Example1()
    ex1.ignore_errors = True
    print(ex1.times2(3), '==', 6)
    print(ex1.times2('abc'), '==', 0)

    ex1.ignore_errors = False
    print(ex1.times2(3), '==', 6)
    try:
        # This should raise an error
        # because ex1.ignore_errors ==  False
        ex1.times2('abc')
        print()
    except Exception as e:
        print(e)


    * Example 2
    ****************************************************************************
    class Example2(object):
        # Aways put these two lines at the top of a class which will have some methods which you want to have error handling
        error_handler = ErrorHandler(on_error_return=0)
        ignore_errors = error_handler.ignore_errors

        # This __init__() is not required.  It lets you set ignore_errors
        # in __init__, so you can instantiate MyClass and set the value
        # of ignore_errors in a single line of code.
        def __init__(self, ignore_errors:bool = None):
            if ignore_errors is not None:
                assert(type(ignore_errors) == bool)
                self.ignore_errors = ignore_errors
            self.ignore_errors = ignore_errors

        @error_handler.wrap()
        def times2(self, value_in):
            assert(type(value_in) in (int, float))
            return value_in*2

    ex2 = Example2(ignore_errors = True)
    print(ex2.times2(3), '==', 6)
    print(ex2.times2('abc'), '==', 0)

    ex2 = Example2(ignore_errors = False)  # or: ex2.ignore_errors = False
    print(ex2.times2(3), '==', 6)
    try:
        # This should raise an error
        # because ex1.ignore_errors ==  False
        ex2.times2('abc')
        print()
    except Exception as e:
        print(e)
    """

    def __init__(self):
        self._instance_ignore_errors = defaultdict(lambda: False)
        self.on_error_return = False

    @property
    def ignore_errors(self):
        return ErrorHandler._ErrorHandlerIgnoreErrorsDescriptor(self._instance_ignore_errors)

    def wrap(self, on_error_return = None):
        if on_error_return is None:
            on_error_return = self.on_error_return
        def wrap(func):
            def wrapper(*args, **kwargs):
                instance = args[0]
                try:
                    return func(*args, **kwargs)
                except Exception as ex:
                    if self._instance_ignore_errors[instance]:
                        return on_error_return
                    else:
                        raise ex
            return wrapper
        return wrap

    class _ErrorHandlerIgnoreErrorsDescriptor(object):
        def __init__(self, d):
            self.instance_ignore_errors = d


        def __get__(self, instance, owner):
            return self.instance_ignore_errors[instance]

        def __set__(self, instance, value):
            self.instance_ignore_errors[instance] = value


