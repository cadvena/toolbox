"""
Keeps PC from sleeping while a long running python process compeletes its work.
Adapted from: 
    https://stackoverflow.com/questions/57647034/prevent-sleep-mode-python-wakelock-on-python
Posted by: 
    https://stackoverflow.com/users/6423074/pedro on May 22, 2020
Developer called it StandbyLock, but I renamed it KeepAwake.


Using it is very simple. You may opt for the decorator approach using keep_awake 
or via KeepAwake as a context manager:

## decorator
@keep_awake
def some_function(*args, **kwargs):
    # While some_function is executing, your system will stay awake.
    # do something lazy here...
    pass

## context manager
with KeepAwake():
    # ...or do something lazy here instead
    pass

Note: There are still some caveats, as Linux may require sudo privileges and 
OS X (Darwin) is not tested yet.
"""

from functools import wraps
import platform


class MetaKeepAwake(type):
    """
    """

    SYSTEM = platform.system()

    def __new__(cls, name: str, bases: tuple, attrs: dict) -> type:
        if not ('inhibit' in attrs and 'release' in attrs):
            raise TypeError("Missing implementations for classmethods 'inhibit(cls)' and 'release(cls)'.")
        else:
            if name == 'KeepAwake':
                cls._superclass = super().__new__(cls, name, bases, attrs)
                return cls._superclass
            if cls.SYSTEM.upper() in name.upper():
                if not hasattr(cls, '_superclass'):
                    raise ValueError("Class 'KeepAwake' must be implemented.")
                cls._superclass._subclass = super().__new__(cls, name, bases, attrs)
                return cls._superclass._subclass
            else:
                return super().__new__(cls, name, bases, attrs)


class KeepAwake(metaclass=MetaKeepAwake):
    """
    """

    _subclass = None

    @classmethod
    def inhibit(cls):
        if cls._subclass is None:
            raise OSError(f"There is no 'KeepAwake' implementation for OS '{platform.system()}'.")
        else:
            return cls._subclass.inhibit()

    @classmethod
    def release(cls):
        if cls._subclass is None:
            raise OSError(f"There is no 'KeepAwake' implementation for OS '{platform.system()}'.")
        else:
            return cls._subclass.release()

    def __enter__(self, *args, **kwargs):
        self.inhibit()
        return self

    def __exit__(self, *args, **kwargs):
        self.release()


class WindowsKeepAwake(KeepAwake):
    """
    """

    ES_CONTINUOUS      = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

    INHIBIT = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    RELEASE = ES_CONTINUOUS

    @classmethod
    def inhibit(cls):
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(cls.INHIBIT)

    @classmethod
    def release(cls):
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(cls.RELEASE)


class LinuxKeepAwake(metaclass=MetaKeepAwake):
    """
    """

    COMMAND = 'systemctl'
    ARGS = ['sleep.target', 'suspend.target', 'hibernate.target', 'hybrid-sleep.target']

    @classmethod
    def inhibit(cls):
        import subprocess
        subprocess.run([cls.COMMAND, 'mask', *cls.ARGS])

    @classmethod
    def release(cls):
        import subprocess
        subprocess.run([cls.COMMAND, 'unmask', *cls.ARGS])


class DarwinKeepAwake(metaclass=MetaKeepAwake):
    """
    """

    COMMAND = 'caffeinate'
    BREAK = b'\003'

    _process = None

    @classmethod
    def inhibit(cls):
        from subprocess import Popen, PIPE
        cls._process = Popen([cls.COMMAND], stdin=PIPE, stdout=PIPE)

    @classmethod
    def release(cls):
        cls._process.stdin.write(cls.BREAK)
        cls._process.stdin.flush()
        cls._process.stdin.close()
        cls._process.wait()


def keep_awake(callback):
    """ keep_awake(callable) -> callable
        This decorator guarantees that the system will not enter standby mode while 'callable' is running.
    """
    @wraps(callback)
    def new_callback(*args, **kwargs):
        with KeepAwake():
            return callback(*args, **kwargs)
    return new_callback