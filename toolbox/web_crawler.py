r"""
main functions:

    link_check confirms that when "response = requests.get(link)" is run,
        response.ok == True.  For ftp, verifies the file by attempting to get file size.
        1) attempt to open header
        2) attempt to get a successful response
        3) if FTP, attempt to download file
        4) return a 2-item tuple of success, status424

    deep_link_check
        Check a url/link to see if it is "ok." Always checks that the link header
        for an ok status.
        -- If local_file_path is provided, also checks that:
            server file size == local_file_path file size and
        -- If hash_check, check that: the server file and local_file_path hashes match.

    check_links_from_file
        Runs deep_link_check() for a list of links specified in argument: input_file.
        See check_links_from_file's docstring for information about input_file.
        Results are saved to output_file.

    broken_link_finder
        Checks for broken links on a specific web page(s) as specified by the urls argument.
        This is not a recursive function.

Like other toolbox modules, this one gets the most general configruation information
from the toolbox config file.  You can find its location
(e.g., C:\Users\username\AppData\Roaming\toolbox\toolbox.cfg)
by running the following in the python terminal:
    >>> import toolbox
    >>> print('toolbox config file (tb_cfg._file):', toolbox.tb_cfg._file)

In that config file, you will find an entry for "WEB_CRAWLER_INI", which specifies
where this module will look for the web_crawler.ini file.  The ini file contains
configuration information specific to the web_crawler module.  This is intentional,
because the ini file is intended to be on a network share and be identical for
everyone in TSD.  In the future, this ini file should probably be converted to a
config file managed by toolbox.config.Config instead of built-in module
configparser.ConfigParser.

Function call heirarchy:
    Main functions call heirarchy:
        link_check
        deep_link_check
            base_url
            webpage_contains_url
                get_links_from_webpage
                    base_url
                    clean_url
                clean_url
        check_links_from_file
            view_file
        broken_link_finder
            get_links_from_webpage
                base_url
                clean_url
            view_file
    Supporrting functions call heirarchy:
        get_links_from_webpage
            base_url
            clean_url
        def base_url
        clean_url
        save_response - not used
        view_file
        webpage_contains_url calls
            get_links_from_webpage
                base_url
                clean_url
            clean_url
"""

import time
# import ftplib
from bs4 import BeautifulSoup
# from toolbox import pjmrequests as requests
import requests
import requests.exceptions
from urllib.parse import urlsplit
from urllib.parse import urljoin
import os
import pandas as pd  # pandas 1.1.5 or higher.
from toolbox.file_util.hash import hash_match  # from tsd-python repo
from toolbox.timer import Timer
import subprocess
from configparser import ConfigParser, NoSectionError
from pprint import pprint

try:
    import html5lib
except ImportError:
    pass
from typing import Union
from collections.abc import Iterable
from datetime import datetime as dtdt
from toolbox.file_util import ez_ftp
from toolbox import appdirs, tb_cfg
from toolbox import temp_file
from toolbox.swiss_army import is_valid_url

from warnings import warn

try:
    # from toolbox.path import Path
    from toolbox.pathlib import *
    from toolbox.pathlib import Path
except Exception as e:
    msg = f'Failed to import Path from toolbox.path. Will use pathlib.Path' \
          + f' instead.  {e}'
    warn(message = msg)
    from pathlib import Path

"""
Requires pandas 1.1.5 or higher.
"""

# ##############################################################################
# Configuration
# ##############################################################################

config_file = tb_cfg['WEB_CRAWLER_INI']
# config_dir = Path(user_config_dir())
# # If config_dir does nto exist, create it
# config_dir.mkdir(parents = True, exist_ok = True)
# # config_file = os.path.join(config_dir, 'web_crawler.ini')
# config_file = Path(config_dir.joinpath('web_crawler.ini'))
# TODO: if cannot find ini file, write one from this string.
ini_text = """[DEFAULT]
DEFAULT_CSV_VIEWER = excel.exe

[RUN]
# Run settings must be set to true/false
RUN_CHECK_LINKS_FROM_FILE = True
RUN_BROKEN_LINK_FINDER = False
RUN_EXAMPLES = False

[CHECK_LINKS_FROM_FILE]
HASH_CHECK = False]
DIR_HOME = \\corp.pjm.com\shares\TransmissionServices\TSI\Compliance\OASISWebChecker
DIR_IN = %(DIR_HOME)s\inputs
DIR_OUT = %(DIR_HOME)s\outputs
DEFAULT_LINKS_CSV = %(DIR_HOME)s\links_to_check.csv
DEFAULT_RESULTS_CSV = %(DIR_OUT)s\links_to_check_results.csv

[BROKEN_LINKS_FINDER]
# Pages on which to search for broken links (1-deep, no recursion)
CHECK_LINKS_ON = https://www.pjm.com/markets-and-operations/etools/oasis.aspx
# CHECK_LINKS_ON = https://www.pjm.com/markets-and-operations/etools/oasis.aspx, https://www.pjm.com/markets-and-operations/etools/oasis/merch-trans-facilities, https://www.pjm.com/markets-and-operations/etools/oasis/special-notices, https://www.pjm.com/markets-and-operations/etools/oasis/system-information, https://www.pjm.com/markets-and-operations/etools/oasis/atc-information, https://www.pjm.com/markets-and-operations/etools/oasis/oasis-reference,https://www.pjm.com/markets-and-operations/etools/oasis/conf-reserv, https://www.pjm.com/markets-and-operations/etools/oasis/outage-accel, https://www.pjm.com/markets-and-operations/etools/oasis/order-890

EXCLUDE_LINKS_STARTING_WITH = mailto, http://www.linkedin.com/, https://videos.pjm.com/, https://dataminer2.pjm, https://www.pjm.com/-/media/etools/oasis/ppl-fac-008-facility-list.ashx, https://pjm.force.com, http://www.naesb.org, http://www.youtube.com, http://oasis.pjm.com/system.htm, http://oasis.pjm.com/drate.html, http://twitter.com, http://insidelines.pjm.com, https://urldefense.proofpoint.com,
"""

if not os.path.exists(config_file):
    default_config_file = os.path.join(Path(__file__).parent.absolute(), 'web_crawler.ini')
    default_config_file = Path(default_config_file)
    s = f'\nCopying webcrawler config file from {default_config_file}' \
        + ' to {config_file}'
    print(s)
    try:
        shutil.copy(default_config_file, config_file)
    except FileNotFoundError:
        config_file = default_config_file

# read configuration file (ini file)
# https://docs.python.org/3/library/configparser.html#module-configparser

# config_dir = Path(__file__).parent.absolute()
config_file = os.path.join(Path(__file__).parent.absolute(), 'web_crawler.ini')
cfg = ConfigParser()
cfg.read(config_file)
print(f'\nwebcrawler.py config file: {config_file}')


def cfg_default(section: str, option: str, default_value, write_value: bool = False):
    try:
        return cfg[section][option]
    except NoSectionError:
        if write_value:
            cfg[section][option] = default_value
        return default_value
    except KeyError:
        if write_value:
            cfg[section][option] = default_value
        return default_value


def cfg_default_boolean(section: str, option: str, default_value: bool, write_value: bool = False):
    try:
        return cfg.getboolean(section = section, option = option)
    except NoSectionError:
        if write_value:
            cfg[section][option] = default_value
        return default_value
    except Exception as e:
        if write_value:
            cfg[section][option] = default_value
        return default_value


if len(cfg) > 0:
    # DEFAULT
    # DEFAULT_CSV_VIEWER = cfg['DEFAULT']['DEFAULT_CSV_VIEWER']
    DEFAULT_CSV_VIEWER = cfg_default('DEFAULT', 'DEFAULT_CSV_VIEWER', 'excel.exe')

    # RUN
    # RUN_BROKEN_LINK_FINDER = cfg.getboolean(section= 'RUN',
    #                                         option = 'RUN_BROKEN_LINK_FINDER')
    RUN_BROKEN_LINK_FINDER = cfg_default_boolean(section = 'RUN',
                                                 option = 'RUN_BROKEN_LINK_FINDER',
                                                 default_value = False)
    # RUN_CHECK_LINKS_FROM_FILE = cfg.getboolean(section= 'RUN',
    #                                            option = 'RUN_CHECK_LINKS_FROM_FILE')
    RUN_CHECK_LINKS_FROM_FILE = cfg_default_boolean(section = 'RUN',
                                                    option = 'RUN_CHECK_LINKS_FROM_FILE',
                                                    default_value = False)
    # RUN_EXAMPLES = cfg.getboolean(section='RUN', option = 'RUN_EXAMPLES')
    RUN_EXAMPLES = cfg_default_boolean(section = 'RUN',
                                       option = 'RUN_EXAMPLES',
                                       default_value = False)

    # CHECK_LINKS_FROM_FILE
    # HASH_CHECK = cfg['CHECK_LINKS_FROM_FILE']['HASH_CHECK']
    HASH_CHECK = cfg_default('CHECK_LINKS_FROM_FILE', 'HASH_CHECK', True)
    # DIR_HOME = cfg['CHECK_LINKS_FROM_FILE']['DIR_HOME'] or os.getcwd()
    DIR_HOME = cfg_default('CHECK_LINKS_FROM_FILE', 'DIR_HOME', os.getcwd())
    # DIR_IN = cfg['CHECK_LINKS_FROM_FILE']['DIR_IN'] or os.path.join(DIR_HOME, 'inputs')
    DIR_IN = cfg_default('CHECK_LINKS_FROM_FILE', 'DIR_IN', os.path.join(DIR_HOME, 'inputs'))
    # DIR_OUT = cfg['CHECK_LINKS_FROM_FILE']['DIR_OUT'] or os.path.join(DIR_HOME, 'outputs')
    DIR_OUT = cfg_default('CHECK_LINKS_FROM_FILE', 'DIR_OUT', os.path.join(DIR_HOME, 'outputs'))
    # DEFAULT_LINKS_CSV = cfg['CHECK_LINKS_FROM_FILE']['DEFAULT_LINKS_CSV']
    DEFAULT_LINKS_CSV = cfg_default('CHECK_LINKS_FROM_FILE', 'DEFAULT_LINKS_CSV', '')
    # DEFAULT_RESULTS_CSV = cfg['CHECK_LINKS_FROM_FILE']['DEFAULT_RESULTS_CSV']
    DEFAULT_RESULTS_CSV = cfg_default('CHECK_LINKS_FROM_FILE', 'DEFAULT_RESULTS_CSV', '')

    # BROKEN_LINKS_FINDER
    CHECK_LINKS_ON = cfg_default('BROKEN_LINKS_FINDER', 'CHECK_LINKS_ON', '')
    CHECK_LINKS_ON = [s.strip() for s in CHECK_LINKS_ON.split(',')]
    # CHECK_LINKS_ON = CHECK_LINKS_ON.split(',')
    EXCLUDE_LINKS_STARTING_WITH = cfg_default('BROKEN_LINKS_FINDER',
                                              'EXCLUDE_LINKS_STARTING_WITH', '')
    EXCLUDE_LINKS_STARTING_WITH = [s.strip() for s in
                                   EXCLUDE_LINKS_STARTING_WITH.split(',')]

    try:
        print('type(cfg): ', type(cfg))
        with open('example.ini', 'w') as f:
            cfg.write(f)
    except Exception as e:
        s = f'Unable to update webcrawler config file "{config_file}" with' \
            + f' default values.  Changes not saved.  {e}'
        warn(s)


# else:
#     raise FileNotFoundError(config_file)
# ##############################################################################
# Supporting Functions
# ##############################################################################

def base_url(url):
    parts = urlsplit(url)
    return f'{parts.scheme}://{parts.netloc}'


def clean_url(precleaned_url):
    if not precleaned_url:
        precleaned_url = ''
    result = precleaned_url.strip()
    while result.endswith('/'):
        result = result[:-1]
    return result


def get_links_from_webpage(url: str,
                           full_links: bool = True,
                           separate_foreign: bool = False,
                           exclude_prefixes: Iterable = EXCLUDE_LINKS_STARTING_WITH) -> dict:
    """
    Returns unique links contained on a webpage (as a dict of sets)
    :param url: the URL to open and search
    :param full_links: bool: True: return fully qualified links
                             False: return links exactly as presented
    :param separate_foreign: bool:
            True: return a dictionary of sets:
                    {'local_urls': local_urls, 'foreign_urls': foreign_urls}
            False: return a dictionary of sets:
                    {'urls': local_urls | foreign_urls}
    :param exclude_prefixes: list-like: list of prefixes.  If any found link
                    starts with a prefix in this list, that link will be
                    excluded from the returned dict.
    :return: a dictionary of one or two sets, depending on the value of separate_foreign
    """
    if type(exclude_prefixes) == type(None):
        exclude_prefixes = []
    elif type(exclude_prefixes) == str:
        exclude_prefixes = [exclude_prefixes]

    local_urls = set()
    foreign_urls = set()  # external URLs

    # get base url
    parts = urlsplit(url)
    base_url = f'{parts.scheme}://{parts.netloc}' or parts.path
    strip_base = parts.netloc.replace('www.', '')
    path = url[:url.rfind('/') + 1]

    try:
        response_txt = requests.get(url).text
    except requests.exceptions.MissingSchema as e:
        if separate_foreign:
            return {'local_urls': set(), 'foreign_urls': set()}
        else:
            return {'urls': set()}
    try:
        soup = BeautifulSoup(response_txt, features = 'lxml')
    except AttributeError as e:
        warn("BeautifulSoup unable to parse using 'lxml'.  Trying 'html5lib'.")
        soup = BeautifulSoup(response_txt, features = 'html5lib')
    links = soup.find_all('a')
    anchors = [link.get('href') for link in links]

    for anchor in anchors:
        if anchor is None or anchor in ['', '#']:
            continue
        anchor = clean_url(anchor)
        anchor.strip()
        if len(exclude_prefixes) > 0 \
                and any([anchor.startswith(prefix) for prefix in exclude_prefixes]):
            # This anchor (i.e., url) starts with a prefix in exclude_prefixes,
            # so we will exclude it from the returned dict.
            continue
        else:
            pass
        if anchor == '#' \
                or 'javascript:void(0)' in anchor \
                or anchor.startswith('mailto:'):
            pass
        if anchor.startswith('/'):
            if full_links:
                anchor = base_url + anchor
            local_urls.add(anchor)
        elif strip_base in anchor:
            local_urls.add(anchor)
        elif anchor.startswith('ftp://') \
                and 'pjm.com' in anchor:
            local_urls.add(anchor)
        elif anchor.startswith('mailto:') \
                and 'pjm.com' in anchor:
            local_urls.add(anchor)
        elif anchor.startswith('http'):
            local_urls.add(anchor)
        else:
            # None of the expected prefixes (mailto, ftp, http) found
            # so assume it is a partial reference.
            if full_links:
                # since anchor is a partial reference and we want a full
                # reference, prepend the path of url to anchor.
                anchor = path + anchor
            local_urls.add(anchor)

    # return the result, a set of sets
    if separate_foreign:
        res = {'local_urls': local_urls, 'foreign_urls': foreign_urls}
    else:
        res = {'urls': local_urls | foreign_urls}
    return res


def webpage_contains_url(parent_url: str, child_url: str, absolute_path: bool = False):
    """
    checks a web page (parent_url) to see if it contains the child_url.
    :param parent_url: the web page to open and inspect
    :param child_url: the link to find in the context of parent_url.text
    :param absolute_path: if True, child_url must exactly match a link on parent_url
                          if False, child_url must be an ending of any link in parent_url
    :return: True if child_url is found, else False
    """

    # for apples-to-apples comparison, remove training slashes from parent_url and child_url and
    # also strip and leading/lagging whitespace.
    parent_url = clean_url(parent_url)
    child_url = clean_url(child_url)

    if not parent_url or not child_url:
        return False

    # Retrieve all links contained on page parent_url
    links = get_links_from_webpage(url = parent_url,
                                   full_links = True,
                                   separate_foreign = False,
                                   exclude_prefixes = [])['urls']

    links = [clean_url(link) for link in links]
    # if looking for exact match of child_url to link form parent_url
    if absolute_path:
        return child_url in links
    else:
        for link in links:
            if link.endswith(child_url):
                # found a match
                return True
        # failed to find match
        return False


def save_response(response, save_as: str, mode: str = 'wb') -> tuple:
    """
    Save a requests response to disk.
    Chris Advena
    :param response: the return from requests.get(url)
    :param save_as: download to this location.
                    You may provide a directory and/or filename.
    :param mode: 'wb' or 'w'
    :return: tuple
        if success: (0, filename)
        if fail: (error_code, reason)
    """
    # TODO: save_response is not used.  However, it would be good to find places
    # where a get().text is saved to file and use this.
    dirname, filename = os.path.split(save_as)
    if not dirname:
        dirname = DIR_OUT

    if not os.path.exists(dirname):
        os.mkdir(dirname)

    if not response.ok:
        return -1, f'Error {response.status_code}: {response.reason}'
        # raise ValueError(f'Error {header.status_code}: {header.reason}')

    if not save_as:
        if filename:
            save_as = filename
        else:
            if 'Content-Disposition' in response.headers.keys() and \
                    'filename' in response.headers['Content-Disposition']:
                filename = response.headers['Content-Disposition']
            filename = filename[filename.find('"') + 1:
                                filename.rfind('"')]

            if not filename:
                return -3, 'save_as not provided and unable to retrieve file ' \
                           'name from response.'

    if not os.path.abspath(save_as) == save_as:
        save_as = os.path.join(dirname, save_as)

    with open(save_as, mode = mode) as writer:
        writer.write(response.content)

    return 0, filename


def view_file(filename: str, viewer: str = DEFAULT_CSV_VIEWER):
    subprocess.DETACHED_PROCESS = True
    try:
        subprocess.Popen(f'{viewer} "{filename}"')
        return True
    except FileNotFoundError:
        return False


# ##############################################################################
# Main Functions
# ##############################################################################
def link_check(link: str):
    """
    link_check confirms that when "response = requests.get(link)" is run,
    response.ok == True.  For ftp, verifies the file by attempting to get file size.
    1) attempt to open header
    2) attempt to get a successful response
    3) if FTP, attempt to download file
    4) return a 2-item tuple of success, status424

    :param link: url (http or ftp) to check.
    :return: tuple(success, status)
        success: True/False
        status: descriptive status
    """
    link = link.strip()
    try:
        head = requests.head(link)
        success = head.ok
        status = "Retrieved header from: {link}"
        try:
            response = requests.get(link)
            success = response.ok
            status = "Received response from: {link}"
        except Exception as e:
            success = False
            status = f"{e}.  Retrieved header but failed to open page: {link}"

    except Exception as e:
        success = False
        status = f"{e}.  Failed to retrieved header from: {link}"

    if link.startswith('ftp'):
        # success = ez_ftp.exists(link)
        # if success:
        #     status = f"FTP file found: {link}"
        # else:
        #     status = f"FTP file not found: {link}"
        # get stats from ftp server
        stats = ez_ftp.stats(link)
        basename = stats.basename
        file_size = stats.size
        if not basename:
            success = False
            status = f"FTP file not found: {link}"
        elif type(basename) == str:
            if file_size > 0:
                success = True
                status = f"FTP file found: {link}"
            else:
                success = False
                status = f"FTP file is empty: {link}"
        else:
            success = False
            status = f"Unexpected error verifying FTP file: {link}"

    return success, status


# def ftp_file_check(ftp_url, )

def deep_link_check(url, local_file_path = None, hash_check: bool = HASH_CHECK,
                    contains_url: str = '', description = '',
                    posted_after: Union[dtdt, None] = None):
    """
    Check a url/link to see if it is "ok"
    Always checks that the link header for an ok status.
    If local_file_path is provided, also checks that:
        server file size == local_file_path file size and
        if hash_check, that the server file and local_file_path hashes match.
    :param url: the url to check
    :param local_file_path: if you wish to compare a local file to the
                            url, provide the pathname here
    :param hash_check: True: hash check the file at the url to the file
                             at local_file_path.
    :param contains_url: optional: if provided, check that url page contains a
                         link matching contains_url
    :param description: optional: description of link being checked
    :param posted_after: if provided, validate that the posting datetime
                         of url > posted_after
    :return: dict summarizing the result of the link check.
            { 'url': str, 'status': int, 'reason': str, 'size on server': int,
              'downloaded file size': int, 'orig file size': -int,
              'contained url code': 0/1/2, 'contained url reason': str,
              'response header': str
            }
            where 'contained url code' in [0, 1, 2]
                0: Not Applicable
                1: Found
                2: Not Found
    """
    # dtdt(year=dtdt.now().year-20, month=1, day=1)
    # Initialize result dict

    res: dict = {
        'success': False,
        'description': description,
        'url': url,
        'status': None,
        'reason': '',
        'contained url': contains_url.strip(),
        'contained url status': None,
        'contained url reason': '',
        'contained url header': None,
        'size on server': None,
        'downloaded file size': None,
        'orig file size': None,
        'header': None,
        }

    # ######################################################################
    # Validate inputs
    # ######################################################################
    if posted_after:
        # TODO: add validation
        # in later sections
        raise NotImplementedError
        # https://docs.python.org/3/library/ftplib.html

    if hash_check and not local_file_path:
        # if local_file_path not provided, skip hash check, even if it was requested.
        hash_check = False

    # if not any([url.lower().startswith(s) for s in ['ftp://', 'ftps://', 'http://', 'https://',
    #                                                 ]]):
    if not is_valid_url(url):
        # If request not for a URL, then success = False.
        res['success'] = False
        res['status'] = 990
        res['reason'] = f'Url "{url}" must start with "ftp" or "http".'
        return res
    elif url.startswith('ftp') and contains_url:
        # If url is FTP, then url is a file, so contains_url has not meaning and must be None.
        res['status'] = 992
        res['reason'] = 'url starts with "ftp", so contains_url must be None.'
        return res
    elif contains_url and local_file_path:
        # contains_url is used to confirm that the page at url contains another url.
        # local_file_path is used to indicate a local good copy of a file to be compared to
        # the file downloaded from url.
        # These are different checks the must be run with separate calls to this function.
        res['success'] = False
        res['status'] = 988
        res['reason'] = f'You cannot provide both local_file_path and contains_url.  They ' \
                        f'are mutually exclusive.  '
        return res

    # contains_url validation
    if contains_url:
        contains_url = contains_url.strip()
        if not isinstance(contains_url, str):
            # contains_url must be a string
            res['success'] = False
            res['status'] = 989
            res['reason'] = f'contains_url must be a string.  '
            return res

    # ######################################################################
    # Local File Path properties
    # ######################################################################
    # If local_file_path includes fully qualified, absolute path (dir and
    # file.ext), then download the file.  If local_file_path is not a directory
    # or a file, then return success=False

    if local_file_path:
        local_file_path = local_file_path.strip()
        if not isinstance(local_file_path, str):
            # local_file_path must be a string
            res['success'] = False
            res['status'] = 989
            res['reason'] = f'contains_url must be a string.  '
            return res
        elif not os.path.exists(local_file_path):
            # path does not exist (as folder or file)
            res['success'] = False
            res['status'] = 985
            res['reason'] = f'Path does not exist, local_file_path: {local_file_path}'
            return res
        elif os.path.isfile(local_file_path):
            # path exists and is a file
            res['orig file size'] = int(os.path.getsize(local_file_path))
        else:
            # path exists but is not a file
            res['success'] = False
            res['status'] = 979
            res['reason'] = f'local_file_path is not a valid file: {local_file_path}'
            return res

    # ##########################################################################
    # If main url is is FTP - download validate
    # ##########################################################################

    if url.startswith('ftp'):
        # get basic ftp file status (name and size)
        try:
            ftp_stats = ez_ftp.stats(url)
            basename, res['size on server'] = ftp_stats.basename, ftp_stats.size
            # mod_date = ftp_stats.modified
        except Exception as e:
            basename, res['size on server'] = None, None
            # mod_date = None
            res['success'] = False
            res['status'] = 982
            res['reason'] = f'Unexpected IndexError.  {e}'
            return res

        if not local_file_path:
            res['success'] = True
            res['status'] = 211
            res['reason'] = "Warning.  FTP file found.  However, an 'orig file' " \
                            "was not provided for comparison."
            return res
        elif res['size on server'] != 0 and res['size on server'] != res['orig file size']:
            # check file size on server before downloading
            res['success'] = False
            res['reason'] = 984
            res['reason'] = f"File size on server ({res['size on server']}) not equal to  " \
                            f"local file size ({res['orig file size']})"
            return res
        else:
            res['success'] = True
            res['status'] = 9
            res['reason'] = f"File size on server ({res['size on server']}) equals  " \
                            f"local file size ({res['orig file size']})"

        if hash_check:
            try:
                ftp_stats2 = ez_ftp.download(url, tgt_folder = DIR_OUT)
                downloaded_file = ftp_stats2.target_filename
                res['downloaded file size'] = os.path.getsize(ftp_stats2.target_filename)
                res['status'] = 'FTP file retrieved successfully'
                # res['status'], downloaded_file, res['downloaded file size'] = ftp_get(url)
            except IndexError as e:
                res['downloaded file size'] = None
                res['success'] = False
                res['status'] = 978
                res['reason'] = f'Unexpected IndexError downloading from url "{url}".  {e}'
                return res

            if not hash_match(downloaded_file, local_file_path):
                res['success'] = False
                res['status'] = 995
                res['reason'] = 'Hash comparison failed.'
                return res
            else:
                res['success'] = True
                res['status'] = 8
                res['reason'] = 'Hash comparison passed.'

        return res

    # ##########################################################################
    # If main url is is HTTP - download validate
    # ##########################################################################

    elif url.startswith('http'):  # url.startswith('http'):

        # header: get and validate
        # ##################################################################
        try:
            # get url info from header meta-data
            res['header'] = requests.head(url)
            res['status'] = res['header'].status_code
            res['reason'] = res['header'].reason
            res['success'] = True
        except Exception as e:
            # unexpected error getting header from url
            res['status'] = 997
            res['reason'] = str(e)
            res['success'] = False
            return res
        # check header for error
        if not res['header'].ok:
            res['success'] = False
            return res
        elif '404' in res['header'].text:
            # error 3, redirected to a "page not found" page
            res['status'] = -3
            res['reason'] = '404 - Page Not Found'
            res['success'] = False
            return res
        # if we did not get the header and validate it, then return success=False
        if not res['success']:
            return res

        # contains_url
        # ##################################################################

        # If 'contains_url' argument was provided, check that url page contains
        # a link matching contains_url
        if contains_url:  # url is http and contains_url is provided.
            # Check that contains_url is on page url
            # and that you can get the header (metadata)

            # Extract a complete list of URLs that are on url.
            contains_url_found_at_url = webpage_contains_url(parent_url = url,
                                                             child_url = contains_url,
                                                             absolute_path = False)

            if contains_url_found_at_url:
                if contains_url.startswith('ftp:'):
                    # get stats from ftp server
                    stats = ez_ftp.stats(contains_url)
                    basename = stats.basename
                    res['size on server'] = stats.size
                    # fname, res['size on server'] = ftp_file_size(contains_url)
                    if basename:
                        # stats found on ftp server.
                        res['contained url status'] = 208
                        res['contained url reason'] = f'contains_url found on ftp server.'
                        res['contained url header'] = None
                        res['success'] = True

                    else:
                        res['contained url status'] = 983
                        res['contained url reason'] = f'contains_url not found on ftp server.'
                        res['contained url header'] = None
                        res['success'] = False
                        return res
                    del basename
                else:  # cotnains_url starts with http
                    # get contains_url header (metadata)
                    parts = urlsplit(contains_url)
                    if parts.netloc == '':
                        contains_url = urljoin(base_url(url), contains_url)
                    try:
                        temp = requests.head(contains_url)
                        res['contained url status'] = temp.status_code
                        res['contained url reason'] = temp.reason
                        res['contained url header'] = temp.headers
                        res['success'] = True
                        # del temp
                    except requests.exceptions.MissingSchema as e:
                        # Invalid URL
                        res['contained url status'] = 976
                        res['contained url reason'] = f'MissingSchema.  Unable to open ' \
                                                      f'contains_url ' \
                                                      f'({contains_url}): {str(e)}'
                        res['contained url header'] = None
                        res['success'] = False
                        return res
                    except Exception as e:
                        res['contained url status'] = 975
                        res['contained url reason'] = f'Unable to open contains_url ' \
                                                      f'({contains_url}): {str(e)}'
                        res['contained url header'] = None
                        res['success'] = False
                        return res
            else:  # contains_url_found_at_url is False
                res['contained url status'] = 999
                res['contained url reason'] = f'contains_url ({contains_url}) ' \
                                              f'not found in ({url}).  '
                res['success'] = False
                return res
            # If contains_url was valid (found) and local_file_path provided,
            # then compare the file at contains_url (remote file) the local
            # file at local_file_path.
        elif local_file_path:  # url is http and local_file_path is provided.
            # quick file size check before spending reosurces downloading file.
            response = requests.head(url)
            res['size on server'] = int(response.headers['Content-Length'])
            if res['size on server'] != res['orig file size']:
                res['success'] = False
                res['status'] = 974
                res['reason'] = f"File size on server({res['size on server']}) not equal to " \
                                f"local file size {res['orig file size']})"
                return res
            else:
                res['success'] = True
                res['status'] = 10
                res['reason'] = f"File size on server({res['size on server']}) equals " \
                                f"local file size {res['orig file size']})"

            if hash_check:
                # We expect a downloadable file.
                response = requests.get(url)
                res['contained url status'] = response.status_code
                res['contained url reason'] = response.reason
                res['contained url header'] = response.headers
                res['success'] = response.ok
                if not res['success']:
                    return res

                # res['size on server'] was set earlier when reviewing the header.
                # So, this is not needed.
                res['size on server'] = int(res['header'].headers['Content-Length'])

                if not ('Content-Disposition' in response.headers.keys() and
                        'filename' in response.headers['Content-Disposition']):
                    res['status'] = 986
                    res['reason'] = f'Unable to determine name of file on server. '
                    res['success'] = False
                    return res

                tmp_file = temp_file.TempFile()
                # write to temp file
                tmp_file.write(response.content)
                # with open(tmp_file.path) as f:
                #     f.write(response.content)

                # how large is the downloaded temp file?
                res['downloaded file size'] = int(os.path.getsize(tmp_file.path))

                # compare hash of downloaded file to local file (local_file_path)
                if not hash_match(tmp_file.path, local_file_path):
                    res['success'] = False
                    res['status'] = 984
                    res['reason'] = f'Hash comparison failed.  Downloaded temp file' \
                                    f'saved to "{tmp_file.path}" for your review.'
                    tmp_file.delete = False
                    return res
                else:
                    res['success'] = True
                    res['status'] = 208
                    res['reason'] = 'Hash comparison passed.'
                tmp_file.remove()

    elif url.startswith('mailto'):
        res['success'] = False
        res['status'] = 972
        res['reason'] = f'mailto links not implemented'
    else:
        res['success'] = False
        res['status'] = 971
        res['reason'] = f'Unexpected url.  Expect URLs to begin with "ftp", "http" or "mailto"'

    return res


def check_links_from_file(input_file: str = DEFAULT_LINKS_CSV,
                          output_file: str = DEFAULT_RESULTS_CSV,
                          print_each: bool = False,
                          open_results_when_done = True,
                          viewer = DEFAULT_CSV_VIEWER,
                          add_datetime_to_filename: bool = False) -> pd.DataFrame:
    """
    Read in links from csv input_file.  For each link, run deep_link_check() and save
    results to csv output_file.
    The input_file contains the following columns:
        description: a description of the url
        url: a webpage address
        orig_file: the path of an known good copy of the file that should be found at url
        contains_url: a link that should be found direclty on the page with address url
        comment: comment
    :param input_file: a csv file containing columns: description, url,
                        orig_file, contains_url, comment.
    :param output_file: the name of the file in which to save the results. If not provided,
                        then the output is not written to a file.  if True and output_file
                        already exits, then output_file is overwritten.
    :param print_each: If True, print the results of each link check as completed.
    :param open_results_when_done: True/False
    :param viewer: viewer to use to view results, such as notepad.exe or excel.exe.
                    IF open_results_when_done == False, then viewer is ignored.
    :return: pd.DataFrame containing one row containing results for each link checked
    Creates output_file (defined below) with results.
    Output file columns:
        row number: results are produced with row numbers 0, 1, 2, ... taken
                    from the index of the dataframe used herein.
        success: True/False: Did url load successfully?
        description: copy of description from input_file
        url: copy of url from input_file
        status: the http/ftp returned status of url
        reason: the http/ftp returned reason of url
        contained url: copy of contains_url from input_file
        contained url status: the http/ftp returned status of contains_url
        contained url reason: the http/ftp returned reason of contains_url
        contained url header: the http/ftp returned header of contains_url
        size on server: size of the file (if applicable) on the server.  Note
                        this is not expected to match the size of the orig_file
                        if contains_url is an aspx page (i.e., the file is
                        wrapped).
        downloaded file size: if applicable, url is downloaded as a file, and
                              the size of that download file is returned here.
        orig file size: the size of the file on disk at path orig_file
        header: the http/ftp returned header of url

    """
    # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html
    try:
        input_file = input_file or DEFAULT_LINKS_CSV
    except:
        input_file = 'links_to_check.csv'
    output_file = output_file or DEFAULT_RESULTS_CSV
    viewer = viewer or DEFAULT_CSV_VIEWER
    viewer = viewer or 'notepad.exe'

    # Read the input file into a dataframe, input_df.  If input_file argument
    # did not contain a path, then open from DIR_IN.  Save the
    if len(os.path.split(input_file)[0]) == 0:
        # no path provided
        input_file = os.path.join(DIR_HOME, input_file)
    input_df = pd.read_csv(input_file, delimiter = ',')

    res = []
    row_cnt = input_df.shape[0]
    fail_cnt = 0
    for index, row in input_df.iterrows():
        # collect input information from the input file.
        if print_each:
            prt_msg = f"\nChecking {index + 1} of {row_cnt}, {row['description']}: "
            print(prt_msg, row['url'])
        for s in ['description', 'url', 'orig_file', 'contains_url', 'comment']:
            if not isinstance(row[s], str):
                row[s] = ''
        hash_check = len(row[
                             'orig_file'].strip()) > 0  # hash_check = len(row['orig_file'].strip()) > 0  # hash_check = row['orig_file'] == True
        d = deep_link_check(url = row['url'],
                            local_file_path = row['orig_file'],
                            hash_check = hash_check,
                            contains_url = row['contains_url'],
                            description = row['description'])
        res.append(d)
        if d['success']:
            if print_each:
                print(f"    - Passed")
        else:
            fail_cnt += 1
            if print_each:
                print(f"    - Failed: {d['reason']}, {d['contained url reason']}")

    # convert results to dataframe
    res = pd.DataFrame(res)
    # Rearrange columns
    new_index = ['success', 'description', 'url', 'status', 'reason', 'contained url',
                 'contained url status', 'contained url reason', 'contained url header',
                 'size on server', 'downloaded file size',
                 'orig file size', 'header']
    res = res.reindex(new_index, axis = "columns")

    if fail_cnt > 0:
        err_df = res.copy()
        err_df = err_df[err_df.success == False]
        err_df = err_df[['description', 'status', 'reason',
                         'contained url status', 'contained url reason']]
        print('*' * 60, '\n')
        print(f'{fail_cnt} link check failed\n')
        pprint(err_df)
        print('*' * 60, '\n')

    # If output_file (an argument to this function) is provided, then save the results
    # to the out_put file.  Also, if output_file contains only the basename (file.ext,
    # not folder), then save to the default directory, DIR_OUT.
    if output_file:
        # save to file

        # insert datestring into a filename (before the suffix)
        def insert_datestr(s: str):
            s, ext = os.path.splitext(s)
            return s + '_' + dtdt.now().strftime('%Y%m%d_%H%M%S') + ext

        # optionally, add timestamp to filename
        if add_datetime_to_filename:
            output_file = insert_datestr(output_file)

        # if no folder provided in output_file name, then save to DIR_OUT
        if os.path.split(output_file)[0] == '':
            # no path provided
            output_file = os.path.join(DIR_OUT, output_file)

        try:
            # write to file
            res.to_csv(output_file)
        except Exception as e:
            msg = f'Unable to save as "{output_file}". '
            # if we haven't already, insert timestamp into filename
            if not add_datetime_to_filename: output_file = insert_datestr(output_file)
            try:
                res.to_csv(output_file)
                msg += f'Saved to "{output_file}". {e}'
                warn(msg)
            except Exception as e:
                # change the folder in which to save
                basename = os.path.basename(output_file)
                fldr = appdirs.user_data_dir('webcrawler')
                output_file = os.path.join(fldr, basename)
                mkdir2(new_path = fldr, parents = True, exist_ok = True)
                # write to file
                res.to_csv(output_file)
                msg += f'Saved to "{output_file}". {e}'
                warn(msg)

    # Open results if argument open_results_when_done is True.
    if open_results_when_done:
        # open result file in viewer text editor).
        view_file(filename = output_file, viewer = viewer)

    return res


def broken_link_finder(urls: Union[str, list, tuple, set],
                       print_to_console: bool = False,
                       file_out = None,
                       viewer = DEFAULT_CSV_VIEWER,
                       open_results_when_done = True,
                       exclude_prefixes: Iterable = EXCLUDE_LINKS_STARTING_WITH):
    """
    Checks for broken links on a specific web page(s) as specified by the urls argument.
    :param urls: the url or urls to check.
    :param print_to_console: True / False -- print each link to console while checking.
    :param file_out: if not None, name of file to which to write broken link
                     checker output
    :param viewer: program to use to open and view the results (csv file)
    :param open_results_when_done: True/False
    :param exclude_prefixes: list-like
    :return: list of sets of broken_urls, local_urls, foreign_urls, processed_urls
    """

    start_time = time.time()

    working_urls: List[Any] = []
    broken_urls: List[Any] = []

    if type(exclude_prefixes) == str:
        exclude_prefixes = [exclude_prefixes]
    if 'mailto' not in exclude_prefixes:
        exclude_prefixes = list(exclude_prefixes)
        exclude_prefixes.append('mailto')

    if type(urls) == str:
        urls = [urls]

    links = []
    for url in urls:
        lst = get_links_from_webpage(url, full_links = True, exclude_prefixes = exclude_prefixes)
        links += lst['urls']

    # remove duplicates
    links = set(links)

    tot = len(links)
    cnt = 0
    for link in links:
        if print_to_console:
            cnt += 1
            print(f'Checking link {cnt} of {tot}: {link}')
        try:
            # TODO: should probably leverage link_check instead of repeating code.
            # compare the code in this function and link_check to see what's up.
            head = requests.head(link)
            success = head.ok
            status = "Retrieved header from: {link}"
            try:
                response = requests.get(link)
                success = response.ok
                status = "Received response from: {link}"
            except Exception as e:
                success = False
                status = f"{e}.  Retrieved header but failed to open page: {link}"

        except Exception as e:
            success = False
            status = f"{e}.  Failed to retrieved header from: {link}"

        if link.startswith('ftp:'):
            # get stats from ftp server
            stats = ez_ftp.stats(link)
            filename = stats.basename
            file_size = stats.size
            # filename, file_size = ftp_file_size(link)
            if not filename:
                success = False
                status = f"FTP file not found: {link}"
            if type(filename) == str:
                if file_size > 0:
                    success = True
                    status = f"FTP file found: {link}"
                else:
                    success = False
                    status = f"FTP file is empty: {link}"
            else:
                success = False
                status = f"{file_size}.  FTP file: {link}"

        if success:
            # found a broken link
            working_urls.append((link, success, status))
        else:
            broken_urls.append((link, success, status))

    processed_urls = working_urls + broken_urls

    if file_out:
        df = pd.DataFrame(data = processed_urls, index = None,
                          columns = ['link', 'success', 'header'])
        df.to_csv(path_or_buf = file_out, sep = ',', header = True)
        if open_results_when_done:
            # open result file in viewer text editor).
            view_file(filename = file_out, viewer = viewer)

    # Done recursive loop.  Report results.

    stop_time = time.time()
    run_time = stop_time - start_time
    if print_to_console:
        print(f'\n\nChecked: {len(processed_urls)} links in {run_time} seconds')
        print(f'\nFound {len(broken_urls)} BROKEN LINKS: \n', broken_urls)

    # Return results.
    ReturnTuple = namedtuple('ReturnTuple', 'processed_urls broken_urls run_time')
    return ReturnTuple(processed_urls, broken_urls, run_time)


# ##############################################################################
# examples
# ##############################################################################

def examples():
    # set each: True = run, False = skip
    # ftp_get_ex = True
    get_links_from_webpage_ex = False
    webpage_contains_url_ex = False
    deep_link_check_ex = False
    broken_link_finder_ex = False
    check_links_from_file_ex = True

    # if ftp_get_ex:
    #     # ftp example
    #     file_url = 'ftp://ftp.pjm.com/pub/oasis/AFC.csv'
    #     res = ftp_get(file_url)
    #     # 0 = success
    #     print(res)
    if get_links_from_webpage_ex:
        # example: get_links_from_webpage()
        d = get_links_from_webpage(url = r'https://www.pjm.com/markets-and-operations/etools/oasis',
                                   full_links = True,
                                   separate_foreign = False)
        for k in d.keys():
            print(k)
            print(d[k])
            print()
    if webpage_contains_url_ex:
        # b = webpage_contains_url(parent_url =
        #                          'https://www.pjm.com/markets-and-operations/etools/oasis.aspx',
        #                          child_url = 'http://www.naesb.org')
        # print(b)

        # b = webpage_contains_url(parent_url =
        #                          'https://www.pjm.com/markets-and-operations/etools/oasis/atc-information.aspx',
        #                          child_url = 'ftp://ftp.pjm.com/oasis/ATCID.pdf')
        # print(b)

        # https://www.pjm.com/markets-and-operations/etools/oasis/atc-information.aspx
        # /-/media/etools/oasis/atc-information/Postback-Methodology-GA.pdf
        # ftp://ftp.pjm.com/oasis/Postback-Methodology.pdf

        b = webpage_contains_url(parent_url =
                                 'https://www.pjm.com/markets-and-operations/etools/oasis/atc-information.aspx',
                                 child_url = 'ftp://ftp.pjm.com/oasis/Postback-Methodology.pdf')
        print(b)
    if deep_link_check_ex:
        # # example: deep_link_check()
        # url = 'https://www.pjm.com/markets-and-operations/etools/oasis.aspx'
        # d = deep_link_check(url=url,
        #                local_file_path = '', hash_check = False, contains_url =
        #                'http://www.naesb.org')
        # print(d)

        url = 'https://www.pjm.com/-/media/etools/oasis/pjm-oasis-api-user-guide.ashx'
        local_file = r'C:\temp\pjm-oasis-api-user-guide-orig.pdf'
        d = deep_link_check(url = url,
                            local_file_path = local_file, hash_check = True)
        print(d)

        # example2: deep_link_check()
        url = 'https://www.pjm.com/-/media/etools/oasis/oasis-user-guide.ashx'
        local_file = r'C:\temp\oasis-user-guide-orig.pdf'
        d = deep_link_check(url = url,
                            local_file_path = local_file, hash_check = True)
        print(d)

        # example 3: deep_link_check() - FTP
        url = 'ftp://ftp.pjm.com/oasis/ATCID.pdf'
        local_file = r'C:\temp\ATCID-orig.pdf'
        d = deep_link_check(url = url,
                            local_file_path = local_file, hash_check = True)
        print(d)

    if broken_link_finder_ex:
        # Example use of test broken_link_spider()
        # starting_url = r'https://www.pjm.com/markets-and-operations/etools/oasis'
        starting_url = CHECK_LINKS_ON
        res = broken_link_finder(urls = starting_url,
                                 print_to_console = True)
        print('res: ', res)
        print('\n\nBROKEN LINKS: \n', res.broken_urls)
    if check_links_from_file_ex:
        res = check_links_from_file(DEFAULT_LINKS_CSV, DEFAULT_RESULTS_CSV)
        print(res)


# ##############################################################################
# MAIN
# ##############################################################################

def main():
    tmr = Timer()
    tmr.start('Starting web_crawler.py')

    def print_settings():
        print('toolbox config file (tb_cfg._file):', tb_cfg._file)
        print("web_crawler.ini (tb_cfg['WEB_CRAWLER_INI']):", tb_cfg['WEB_CRAWLER_INI'])
        print("ini run settings:", [x for x in cfg['RUN'].items()])

    print_settings()

    # If folders do not exist, make them
    for fldr in [DIR_HOME,
                 DIR_IN,
                 DIR_OUT
                 ]:
        if not os.path.exists(fldr):
            Path(fldr).mkdir(parents = True)
            # os.mkdir(fldr)
    # Update the [RUN] section of web_crawler.ini to
    # set which of the following sections to run.
    if RUN_EXAMPLES:
        tmr.step('Starting examples link checker.')
        examples()

    if RUN_CHECK_LINKS_FROM_FILE:
        tmr.step('Starting compliance link checker.')
        check_links_from_file(input_file = DEFAULT_LINKS_CSV,
                              output_file = DEFAULT_RESULTS_CSV,
                              viewer = 'excel.exe',
                              open_results_when_done = True,
                              print_each = True)

    if RUN_BROKEN_LINK_FINDER:
        tmr.step('Starting broken_link_spider.')
        broken_link_finder(urls = CHECK_LINKS_ON,
                           print_to_console = True,
                           file_out = os.path.join(DIR_OUT,
                                                   'broken_link_checker_results.csv'),
                           viewer = 'excel.exe',
                           open_results_when_done = False)

    tmr.stop('Finished web_crawler.py.')
    tmr.print_times()

    print_settings()


if __name__ == '__main__':
    main()
