"""
logging: https://docs.python.org/3/howto/logging.html#logging-basic-tutorial

"""

from os import path, remove
# from toolbox import tb_cfg

def log_trimmer(log_file: str, max_log_size: int = 0, trim_ratio = 0.9):
    """
    This function trims the log_file only if needed. The logic is as follows:
    If max_log_size = 0, delete log_file
    Else if file size exceeds max_log_size, remove the first trim_ratio
        percent of the lines.

    :param log_file: filename of log file
    :param max_log_size:
        if max_log_size = 0, delete log_file
        elif file size exceeds max_log_size, trim the first 90% of the lines.
    :param trim_ratio: percentage of lines to remove from beginning of
        log_file IF log size > max_log_size.  trim_ratio ust be > 0 and< = 100.
        If 1 < trim_ratio <= 100, then value is considered a percent
        If 0 < trim_ratio <=1, then value is considered a ratio (fraction)
    :return:
    """
    # logging: https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
    if path.exists(log_file):
            if path.isfile(log_file):
                if max_log_size == 0:
                    remove(log_file)
                elif path.getsize(log_file) > max_log_size:
                    # Remove the first 90% of the lines of the log file.
                    # We will do this by reading the log file, the overriting
                    # the log file with the last 10% of the lines.
                    assert(trim_ratio>0)
                    assert (trim_ratio <= 100)
                    if trim_ratio >= 1:
                        trim_ratio = trim_ratio / 100
                    # read in the log file
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                    # determine lines to keep based on trim_ratio
                    keep_lines = lines[-int(len(lines)*(1-trim_ratio)):]
                    # overwrite the log file with keep_lines, effectively
                    # removing the first trim_ratio percent of lines
                    remove(log_file)
                    with open(log_file, 'w') as f:
                        f.writelines(keep_lines)
