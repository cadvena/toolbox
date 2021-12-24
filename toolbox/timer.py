from time import time
from time import sleep
from pandas import DataFrame
from datetime import datetime as dtdt
from collections import namedtuple
# from toolbox import tb_cfg

# ##############################################################################
# Constants
# ##############################################################################

# FMT is used in _timestamp_to_str() and determines the output format of
# time date in Timer.times.report().
FMT = '%H:%M:%S.%f'


# ##############################################################################
# Timer - the main class
# ##############################################################################
class Timer:
    """
    Timer class for performance timing.
    Times are stored in steps as a list of tuples like:
    [(clock time, 0, note),
     (clock time, step time, elapsed time, note),
     (clock time, step time, elapsed time, note), ...
     (clock time1, step time, elapsed time, note)
    ]
    """
    def __init__(self):
        self._steps = list()
        self._stopped = False
        self._start_time = None
        # self._nano_second_precision = nano_second_precision
        self._times_df = None
        self._times_report = None
        self._now = time
        # if nano_second_precision:
        #     self._now = perf_counter_ns
        # else:
        #     self._now = perf_counter

    @property
    def start_time(self):
        return self._steps[0][0]

    @property
    def stop_time(self):
        if self._stopped:
            return self._steps[-1][0]
        else:
            return None

    @property
    def total_elapsed_time(self):
        if self._stopped:
            return self._steps[-1][2]
        else:
            return None

    @property
    def started(self):
        """ Is the timer started? """
        return len(self._steps) > 0

    @property
    def stopped(self):
        """ Is the timer stopped? """
        # The next if statement is just in case
        # self._stopped was incorrectly set to True.
        if len(self._steps) < 2:
            self._stopped = False
        return self._stopped

    def start(self, note = None):
        """
        Start the timer and return the start time.  If already started, returns
        the already set start time.  To restart the timer, use the restart method.
        :return:
        """
        if len(self._steps) == 0:
            if not note:
                note = 'Starting Timer '
            self._steps = [(self._now(), 0, 0, note)]

    def clear(self):
        """
        Erase all previous data (start, steps and stop).
        """
        self.__init__()
        # self.__init__(nano_second_precision = self._nano_second_precision)

    def restart(self, note = None):
        """
        Restart the timer.
        Restarting the timer erases all previous data (start, steps and stop)
        and runs the start method (setting a new start time).
        """
        self.clear()
        self.start(note = note)

    def stop(self, note = None):
        t = self._now()
        if self.started and not self.stopped:
            self._steps.append((t, t - self._steps[-1][0],
                                t - self._steps[0][0], note))
            self._stopped = True

    @property
    def current_elapsed_time(self):
        """
        If clock is running, returns elapsed time from start, without
        recording a new step.
        :return: current clock time minus start clock time.
        """
        t = self._now()
        if self.stopped:
            return None
        if self.started:
            return  t - self._steps[0][0]
        else:
            return 0

    def step(self, note = None):
        """
        If Timer is running, adds a new timestamp to self._steps.
        """
        t = self._now()
        if self.started and not self.stopped:
            self._steps.append((t, t - self._steps[-1][0],
                                t - self._steps[0][0], note))

    @property
    def last_step(self):
        """
        Get data from the last recorded step (which may be the stop data)
        :return: tuple(clock time, elapsed time, note)
        """
        if self.started:
            return self._steps[-1]
        else:
            return None

    @property
    def times(self):
        if not self.started:
            return None
        # if already created, save time
        elif self.stopped and self._times_df:
            return self._times_df
        else:
            # create dataframe
            df = DataFrame(data = self._steps, columns = ['clock', 'step', 'elapsed', 'note'])
            # if Timer is stopped, then store the results
            if self.stopped:
                self._times_df = df
        return df

    @property
    def status(self):
        tpl = namedtuple()

    @property
    def times_report(self):
        # strftimestamp
        if not self.started:
            return None
        elif self.stopped and self._times_report is not None:
            return self._times_df
        else:
            df = self.times.copy(deep = True)
            df['clock'] = df['clock'].apply(_timestamp_to_str)
            if self.stopped:
                self._times_report = df
            return df

    def print_times(self):
        if self.times_report is not None:
            print(self.times_report[['step', 'elapsed', 'note']])
        else:
            print('No times recorded yet.')

# ##############################################################################
# Supporting functions
# ##############################################################################


def _timestamp_to_str(timestamp_secs: float):
    # Convert a float value for time (e.g., time.time()) to a formatted string
    return dtdt.fromtimestamp(timestamp_secs).strftime(format = FMT)


# ##############################################################################
# Examples
# ##############################################################################

def exmaple1():
    def print_stuff(msg):
        print('\n', msg)
        print('    t.started = ', t.started)
        print('    t.stopped = ', t.started)
        print('    t.last_step = ', t.last_step)
        print('    t.current_elapsed_time = ', t.current_elapsed_time)
        print('    t.total_elapsed_time = ', t.total_elapsed_time)
        print('    t.times_report:')
        t.print_times()

    msg = 'Creating Timer object, t.'
    t = Timer()
    print_stuff(msg)

    sleep(0.1)
    msg = 'Starting timer...'
    t.start(msg)
    print_stuff(msg)

    sleep(0.1)
    msg = 'Record a step (like a stopwatch).'
    t.step(msg)
    print_stuff(msg)

    sleep(0.1)
    msg = 'Record another step (like a stopwatch).'
    t.step(msg)
    print_stuff(msg)

    sleep(0.1)
    msg = 'Stopping timer...'
    t.stop(msg)
    print_stuff(msg)

    sleep(0.1)
    msg = 'Clearing timer...'
    t.clear()
    print_stuff(msg)

    sleep(0.1)
    msg = 'Starting timer...'
    t.start(msg)
    print_stuff(msg)

    sleep(0.1)
    msg = 'Restarting timer...'
    t.restart(msg)
    print_stuff(msg)

    sleep(0.1)
    msg = 'Stopping timer...'
    t.stop(msg)
    print_stuff(msg)


# ##############################################################################
# Main
# ##############################################################################

if __name__ == '__main__':
    exmaple1()
