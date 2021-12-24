# If CLEAR_LOG = True, overwrite log on each run.  Else, append.
# MAX_LOG_SIZE (bytes) is the maximum size of the log file.  If the log file is
# larger than this size upon start of the script, the old log file will be
# deleted.  Note that the log file will exceed the MAX_LOG_SIZE, as this
# parameter is only used at the beginning of the script.
MAX_LOG_SIZE = 50000000
LOG_TRIM_RATIO = 0.9

# Midas_Touch looks for any file in the folder older than NUM_DAYS, and updates
# the modified data of those files to equal now.  If you just want to sync folders,
# set RUN_MIDAS_TOUCH = False
RUN_MIDAS_TOUCH = False
NUM_DAYS = 120
TOUCH_FOLDERS = [r'C:\Personal',
                 r'F:\Personal',
                 r'C:\Projects',
                 r'\\corp.pjm.com\shares\TransmissionServices',
                 r'\\corp.pjm.com\shares\ATC',
                 ]


# Sync the folders?  If you just want to run Midas_Touch, set RUN_SYNC = False.
RUN_SYNC = True
SYNC_FOLDERS = [['backup',
                 r'C:\Users\advena\AppData\Roaming',
                 r'D:\Backup\Users\advena\AppData']
                                ]

LOG_FILE = r'daily_script.log'

PRINT_LOG_TO_CONSOLE = True

# ##############################################################################
# Do NOT change anything below this line
# ##############################################################################
from sys import path
import pathlib
try:
    p = pathlib.Path(__file__).parent.resolve()
    path.insert(0, p)
    try:
        gp = pathlib.Path (__file__).parent.parent.resolve ()
        path.insert (0, gp)
    except:
        print(f'"{p}" not added to sys.path')
except:
    print (f'"{gp}" not added to sys.path')


