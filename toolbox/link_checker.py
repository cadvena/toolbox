import os
import warnings

import bs4
from bs4 import BeautifulSoup
from collections import namedtuple
from datetime import datetime as dtdt
from dateutil.parser import parse as dt2str
import pandas as pd
import re
from requests.models import Response as _Response
from toolbox import tb_cfg, appdirs
from toolbox.config import Config
from toolbox.file_util import backup_file
from toolbox.ez_ftp import FTP  # , StatsTuple
from toolbox.file_util.hash import hash_match
from toolbox.pathlib import Path
from toolbox.swiss_army import is_iterable
toolbox import error_handler
from pprint import pprint
from warnings import warn
from typing import Union
import subprocess
from urllib.parse import urljoin
try:
    from pjmlib import requests
except ImportError as e:
    warn("Unable to import 'pjmlib.requests'.  Using built-in 'requests' instead.")
    import requests
try:
    from requests_html import HTMLSession
except ModuleNotFoundError as e:
    HTMLSession = None
    warnings.warn("Unable to import reqeusts_html.HTMLSession.  "
                  "WegPage.forms() may not work as excpected if argument execute_js == True")
try:
    from toolbox.swiss_army import urlparse
except:
    from urllib.parse import urlparse
# from toolbox.swiss_army import datetime_us_fmt
# import urllib.parse
# from pathlib.py import Path
# from toolbox.swiss_army import is_valid_url

WebPageExceptions = namedtuple('WebPageExceptions', ['head_exception', 'get_exception'])
SaveResult = namedtuple('SaveResult', ['filename', 'exception', 'hash'])

# These are default folders used in the functions below.  However, it is better
# practice to set pass your own preferred directories in the function calls.
dir_home = Path(appdirs.user_data_dir('link_checker', 'toolbox'))
default_config = {
    'LINK_CHECKER': {
        "HASH_CHECK": True,
        "OPEN_RESULTS": True,
        "VERBOSE": True,
        "DIR_HOME": dir_home.str,
        "DIR_IN": dir_home.joinpath("inputs").str,
        "DIR_OUT": dir_home.joinpath("outputs").str,
        "DEFAULT_LINKS_CSV": dir_home.joinpath("links_to_check.csv").str,
        "DEFAULT_RESULTS_CSV":
            dir_home.joinpath("outputs").joinpath("links_to_check_results.csv").str,
        "EXCLUDE_LINKS_STARTING_WITH": [""],
        }
    }
tb_cfg.update_if_none(dict_of_parameters = default_config, recurse = True)
DIR_HOME = tb_cfg['LINK_CHECKER']['DIR_HOME']
DIR_IN = tb_cfg['LINK_CHECKER']['DIR_IN']
DIR_OUT = tb_cfg['LINK_CHECKER']['DIR_OUT']

# BREAK_RESISTANT: bool = True
# if os.environ['username'] == 'advena':
#     BREAK_RESISTANT: bool = False


# ##############################################################################
# WebPage
# ##############################################################################

class WebPageNotLoadedError(Exception):
    pass


class WebPageTimestampError(Exception):
    pass


def domain(url):
    """
    From a url, get top_level.dom from subdom.top_level.dom
    Returns a 2-tuple (top_level, dom)
    """
    result = urlparse(url = url).netloc.split('.')[-2:]
    return tuple(result)


def clean_url(unclean_url):
    if not unclean_url:
        unclean_url = ''
    result = unclean_url.strip()
    while result.endswith('/'):
        result = result[:-1]
    return result


class WebPage:
    error_handler = error_handler.ErrorHandler()
    ignore_errors = error_handler.ignore_errors

    def __init__(self, url: str, cache: bool = True, working_dir = None):
        self.url = clean_url(url)
        parts = urlparse(url)
        if not parts.scheme:
            self.url = "http://" + url
        self._head = None
        self._soup = None
        self._text = None
        self.cache = cache
        self._head_exception = None
        self._get_exception = None
        self._get = None
        self._anchors = None
        self._absolute_urls = None
        self.internal_domain = 'pjm.com'
        self.working_dir = working_dir

    @error_handler.wrap(on_error_return=None)
    def head(self, cache: bool = None):
        """
        Gets the response from HEAD.  If HEAD was already retrieved and cache=True,
        then use previously received response.
        :param cache: True: use cache; False: run HEAD even if already cached.
        :return: response to HEAD (requests.head)
        """
        cache = cache or self.cache
        if self._head is None or not cache:
            try:
                self._head = requests.head(url = self.url)
                self._head_exception = None
            except Exception as e:
                self._head = None
                self._head_exception = e
        return self._head

    @property
    def exceptions(self) -> WebPageExceptions:
        return WebPageExceptions(self._head_exception, self._get_exception)

    def ok(self) -> Union[bool, None]:
        if self._get_exception is None and self._head_exception is None:
            if type(self._head) == _Response or type(self._get) == _Response:
                return True
            self.head()
            if isinstance(self._head_exception, Exception):
                return False
            else:
                return True
        elif self._get_exception == self._head_exception:
            # both are True, False or None
            return self._get_exception
        elif self._get_exception is None:
            return self._head_exception
        elif self._head_exception is None:
            return self._get_exception
        else:
            return False  # self._get_exception and self._head_exception

    @error_handler.wrap(on_error_return=None)
    def get(self, cache: bool = None, execute_js: bool = False, **kwargs) -> Union[_Response, Exception]:
        """
        Gets the response from GET.  If a response was already retrieved and cache=True,
        then use previously received response.
        :param cache: True: use cache; False: run GET even if response already cached.
        :return: response to HEAD (requests.head)
        """
        cache = cache or self.cache
        if self._get is None or not isinstance(self._get, _Response) or not cache:
            try:
                session = None
                if execute_js:
                    try:
                        session = HTMLSession()
                        self._get = session.get(self.url)
                    except:
                        session = None
                if session is None:
                    self._get = requests.get(self.url, **kwargs)
                self._get_exception = None
            except Exception as e:
                self._get = e
                self._get_exception = e
                raise e
        return self._get

    def text(self, cache: bool = None):
        """If self.get() returns a response, return that response, else,
        return the Exception object."""
        cache = cache or self.cache
        response = self.get(cache = cache)
        if isinstance(response, _Response):
            self._text = response.text
        else:
            self._text = self._get
        return self._text

    @error_handler.wrap(on_error_return=None)
    def soup(self, cache: bool = None, execute_js: bool = False, **getkwargs) -> Union[BeautifulSoup, Exception]:
        """ Returns BeautifulSoup(url) or an Exception. """
        cache = cache or self.cache
        # try:
        #     self._soup = BeautifulSoup(self.text(cache=cache), features = 'html5lib')
        # except:
        #     pass

        if self._soup is None or not cache:
            self._text = self.text(cache = cache)
            if isinstance(self._text, Exception):
                self._soup = self._text
            else:
                if execute_js:
                    text = self.get(cache=cache, execute_js=execute_js, **getkwargs)
                else:
                    text = self._text
                try:
                    self._soup = BeautifulSoup(text, features = 'lxml')
                except AttributeError as e:
                    warn("BeautifulSoup unable to parse using 'lxml'.  Trying 'html5lib'.")
                    try:
                        self._soup = BeautifulSoup(text, features = 'html5lib')
                    except Exception as e:
                        self._soup = e
                        raise e
        return self._soup

    @error_handler.wrap(on_error_return=[])
    def anchors(self, cache: bool = None, full_links: bool = False,
                same_domain: bool = False, regex_pattern: str = None):
        """
        Get the anchors found in get(self.url).text (i.e., links from page self.url)
        :param cache:
        :param same_domain: filter results to only URLs in the same domain as self.url
        :param full_links: filter results to only include URLs with full/absolute paths
        :param regex_pattern: filter results to only those matching this regex pattern
        :return: list[str] of URLs found on WebPage (i.e.,  on self.url)
        """
        cache = cache or self.cache
        if self._anchors is None or not cache:
            self._soup = self.soup(cache = cache)
            if isinstance(self._soup, Exception):
                self._anchors = self._soup
            try:
                self._anchors = [urljoin(self.url, clean_url(link.get('href')))
                                 for link in self._soup.find_all('a')]
            except AttributeError as e:
                self._anchors = e
                raise e
                return self._anchors

        result = self._anchors
        if full_links:
            result = [x for x in result if len(urlparse(x).scheme) > 0]
        if same_domain:
            temp = []
            ulr_domain = '.'.join(domain(self.url))
            result = [x for x in result if urlparse(x).netloc.endswith(ulr_domain)
                      or urlparse(x).scheme in ['', 'http', 'https', 'ftp',
                                                'ftps', 'mailto']]
        if regex_pattern:
            result = [x for x in result if re.match(pattern = regex_pattern, string = x)]
        return result

    def absolute_urls(self, cache: bool = None):
        """
        Returns soup.find_all() for "link", "script", "img" and "a"
        :param cache: Iff True and absolute_urls already created/cached, use the cached values
        :type cache: bool

        :return: absolute urls from self._soup
        :rtype:
        """
        cache = cache or self.cache
        if cache and not self._absolute_urls:
            # self.cahce==True and self._absolute_urls was already set, so we can skip the legwork
            # and simply return self._absolute_urls
            pass
        else:
            temp = self._soup.find_all("link")
            for link in self.temp:
                try:
                    link.attrs["href"] = urljoin(self.url, link.attrs["href"])
                except:
                    pass
            self._absolute_urls = temp

            temp = self._soup.find_all("script")
            for script in self._absolute_urls:
                try:
                    script.attrs["src"] = urljoin(self.url, script.attrs["src"])
                except:
                    pass
            self._absolute_urls += temp

            temp = self._soup.find_all("img")
            for img in self._soup.find_all("img"):
                try:
                    img.attrs["src"] = urljoin(self.url, img.attrs["src"])
                except:
                    pass
            self._absolute_urls += temp

            temp = self._soup.find_all("a")
            for a in self._soup.find_all("a"):
                try:
                    a.attrs["href"] = urljoin(self.url, a.attrs["href"])
                except:
                    pass
            self._absolute_urls += temp

        return self._absolute_urls

    def contains_child_url(self, child_url: str, ends_with: bool = True):
        """
        checks self to see if it contains the child_url.
        :param child_url: the link to find in the context of parent_url.text
        :return: True if child_url is found, else False
        """
        child_url = clean_url(child_url)
        if ends_with:
            for anchor in self.anchors():
                if clean_url(anchor).endswith(child_url):
                    return True
        else:
            for anchor in self.anchors():
                if clean_url(anchor) == child_url:
                    return True
        return False

    @error_handler.wrap(on_error_return=[])
    def save_page(self, save_as: str = None, mode: str = 'wb') -> SaveResult:
        """
        Save a requests response to disk.
        :param save_as: download to this location.
                        You may provide a directory and/or filename.
        :param mode: 'wb' or 'w'
        :return: tuple
            if success: (0, filename)
            if fail: (error_code, reason)
        """
        excep = None
        response = self.get()
        if isinstance(response, Exception):
            excep = response

        if not self.ok():
            try:
                raise WebPageNotLoadedError
            except SaveResult as e:
                excep = e
                # raise e
        else:
            if not save_as:
                save_as = os.path.split(self.url)[-1]
                if 'Content-Disposition' in response.headers.keys() and \
                        'filename' in response.headers['Content-Disposition']:
                    save_as = response.headers['Content-Disposition']
                    save_as = save_as[save_as.find('"') + 1:
                                      save_as.rfind('"')]
                if self.working_dir:
                    save_as = Path(self.working_dir).joinpath(save_as)
                save_as = Path(save_as)
            try:
                if not save_as.parent.exists():
                    save_as.parent.mkdir(parents = True)
                if not mode.endswith('b') and isinstance(response.content, bytes):
                    warn(f'"{self.url}" content is bytes.  Saving {save_as} '
                         f'with mode = "wb" instead of "{mode}".')
                    mode = 'wb'
                with open(save_as, mode = mode) as writer:
                    writer.write(response.content)
            except Exception as e:
                excep = e
                raise e
            # SaveResult = namedtuple('SaveResult', ['filename', 'exception', 'hash'])
            return SaveResult(save_as, excep, None)

    def find(self, string: str, insensitive: bool = False) -> list:
        """
        Find location of the 1st occurrence of string on WebPage.
        :param string: str to find on WebPage
        :return: int
        """
        if insensitive:
            return self.text().lower().find(string.lower())
        else:
            return self.text().find(string)

    def get_forms(self, cache: bool = None, execute_js:bool = False) -> bs4.element.ResultSet:
        """
        Returns all form tags found on WebPage
        based on https://www.thepythoncode.com/article/extracting-and-submitting-web-page-forms-in-python/
        """
        cache = cache or self.cache
        # GET request
        soup = self.soup(cache=cache)
        return soup.find_all("form")
    @staticmethod
    def get_form_details(form):  # -> bs4.element.Tag:
        """Returns the HTML details of a form,
        including action, method and list of form controls (inputs, etc)
        based on https://www.thepythoncode.com/article/extracting-and-submitting-web-page-forms-in-python/
        :param form: a form from WebPage.get_forms()
        :type form: bs4.element.ResultSet
        :return: the HTTP response
        :rtype: requests.models.Response
        """
        details = {}
        # get the form action (requested URL)
        action = form.attrs.get("action").lower()
        # get the form method (POST, GET, DELETE, etc)
        # if not specified, GET is the default in HTML
        method = form.attrs.get("method", "get").lower()
        # get all form inputs
        inputs = []
        for input_tag in form.find_all("input"):
            # get type of input form control
            input_type = input_tag.attrs.get("type", "text")
            # get name attribute
            input_name = input_tag.attrs.get("name")
            # get the default value of that input tag
            input_value = input_tag.attrs.get("value", "")
            # add everything to that list
            inputs.append({"type": input_type, "name": input_name, "value": input_value})
        # put everything to the resulting dictionary
        details["action"] = action
        details["method"] = method
        details["inputs"] = inputs
        return details

    def submit_form(self, form, data: dict):
        """
        Use case:  (1) run .get_form_details(form)['inputs'] method to get form details.
                   (2) put your data into a dictionary
                   (3) use this method to pass your data in the form submission.
        Example:
            # create a WebPage object
            page = WebPage('https://wikipedia.org')
            # get all forms from page
            forms = page.get_forms()
            # get the details from the first form, forms[0]
            form_details = page.get_form_details(forms[0])
            # get only the input fields from the form
            input_fields = form_details['inputs']
            # prompt user for form data
            data = {}
            for input_tag in form_details["inputs"]:
                if input_tag["type"] == "hidden":
                    # if it's hidden, use the default value
                    data[input_tag["name"]] = input_tag["value"]
                elif input_tag["type"] != "submit":
                    # all others except submit, prompt the user to set it
                    value = input(f"Enter the value of the field '{input_tag['name']}' (type: {input_tag['type']}): ")
                    data[input_tag["name"]] = value
            response = page.submit_form(forms[0], data)

        based on https://www.thepythoncode.com/article/extracting-and-submitting-web-page-forms-in-python/
        :param form: a form from WebPage.get_forms()
        :type form: bs4.element.ResultSet
        :param data: form data in dict of {tag_name: value, tag_name, value, ...}
        :type data: dict
        :return: the HTTP response as soup
        :rtype: soup  # requests.models.Response
        """
        # TODO WIP: this method not yet tested/verified to work.
        form_details = self.get_form_details(form)

        # Validate that data contains valid input tags
        # get a list of valid input tags for the form
        # # input_tags = []
        # # for input_tag in form_details["inputs"]:
        # #     if input_tag["type"] not in [ "hidden", "submit"]:
        # #         input_tags += [input_tag["name"]]
        # input_tags = [input_tag["name"] for input_tag in form_details["inputs"]
        #               if input_tag["type"] not in ["hidden", "submit"]]
        # for key in data.keys():
        #     assert(key in input_tags)

        url = urljoin(self.url, form_details["action"])

        if form_details["method"] == "post":
            response = requests.post(url=url, data=data)
        elif form_details["method"] == "put":
            response = requests.put(url, data=data)
        elif form_details["method"] == "delete":
            response = requests.delete(url, params=data)
        elif form_details["method"] == "get":
            response = requests.get(url, params=data)
        else:
            raise NotImplementedError(f"method {form_details['method']} not implemented")

        try:
            return BeautifulSoup(response.content, 'html5lib')
        except Exception as e:
            return BeautifulSoup(response.content, "lxml")


# ##############################################################################
# Deep Link Check
# ##############################################################################

links_to_check_csv_columns: list = ['description', 'url', 'orig_file', 'check_child_url', 'comment']
# links_to_check_csv_columns = ['description', 'url', 'orig_file', 'check_child_url',
#                               'permitted_age_days', "permitted_", 'comment']

# result dict
result_template: dict = {
    'success': None,  # True/False: Did url load successfully?
    'description': None,  # copy of description from input_file
    'url': None,  # copy of url from input_file
    'request status': None,  # the http/ftp returned status of url
    'reason': '',  # the http/ftp returned reason of url
    'child url': None,  # copy of check_child_url from input_file
    'child url status': None,  # the http/ftp returned status of check_child_url
    'child url reason': '',  # the http/ftp returned reason of check_child_url
    'child url header': None,  # the http/ftp returned header of check_child_url
    'size on server': None,  # size of the file (if applicable) on the server.
    #   size on server: Note, this is not expected to match the size of the orig_file if
    #                         check_child_url is an aspx page (i.e., the file is wrapped).
    'downloaded file size': None,  # if applicable, url is downloaded as a file
    #   downloaded file size:  if applicable, url is downloaded as a file, and the size of that
    #                         download file is returned here.
    'orig file size': None,  # the size of the file on disk at path orig_file
    'orig file path': None,  # local path to the original file (used for hash check)
    'header': None,  # header returned from http GET
    'timestamp': None  # timestamp returned from FTP file
    }


def deep_link_check(url, local_file_path = None,
                    hash_check: bool = True,
                    check_child_url: str = '',
                    description = '',
                    posted_after: Union[dtdt, None] = None,
                    working_dir = Path()):
    parts = urlparse(url)
    if parts.scheme in ['http', 'https']:
        res = deep_link_check_http(url = url, local_file_path = local_file_path,
                                   hash_check = hash_check,
                                   check_child_url = check_child_url,
                                   description = description,
                                   posted_after = posted_after,
                                   working_dir = working_dir)
    elif parts.scheme in ['ftp', 'ftps']:
        res = deep_link_check_ftp(url = url, local_file_path = local_file_path,
                                  hash_check = hash_check,
                                  check_child_url = check_child_url,
                                  description = description,
                                  posted_after = posted_after,
                                  working_dir = working_dir)
    else:
        res = result_template
        res['success'] = False
        res['reason'] = f'Error: URL Scheme not supported. "{url}" is of scheme {parts.scheme} is ' \
                        f'not supported.'
    return res


@error_handler.wrap(on_error_return=[])
def deep_link_check_http(url, local_file_path = '',
                         hash_check: bool = True,
                         check_child_url: str = '',
                         description = '',
                         posted_after: Union[dtdt, None] = None,  # ignored
                         working_dir = Path()):
    # Initialize from arguments
    url = url.strip()
    local_file_path = local_file_path.strip()
    check_child_url = check_child_url.strip()
    description = description.strip()
    working_dir = working_dir or Path(os.path.cwd)

    # Initialize result dict
    res = None
    res = result_template.copy()
    res['description'] = description
    res['url'] = url
    res['child url'] = check_child_url
    res['orig file path'] = local_file_path

    # Create WebPage object.
    try:
        page: WebPage = WebPage(url, cache = True, working_dir = working_dir)
        res['request status'] = page.get().status_code
        res['reason'] = page.get().reason
        res['success'] = page.get().ok
    except Exception as e:
        res['success'] = False
        res['reason'] = f'Error: Webpage failed unexpectedly. ("{url}") {e}'
        raise e
        return res

    # Compare known good file (local_file_path) to posted file
    if local_file_path:
        # check file size
        try:
            local_file_size = Path(local_file_path).getsize()
        except FileNotFoundError as e:
            res['success'] = False
            res['reason'] = f'Error: Local File Not Found.  local_file_path "{url}" not found.  {e}'
            return res
        except Exception as e:
            res['success'] = False
            res['reason'] = f'Error: File Open Err or.  Cannot open local_file_path "{url}".  {e}'
            raise e
            return res
        try:
            remote_file_size = page.get().headers._store['content-length'][-1]
        except KeyError as e:
            downloaded_file = page.save_page()
            if not downloaded_file.exception:
                try:
                    remote_file_size = Path(downloaded_file.filename).getsize()
                except Exception as e:
                    res['success'] = False
                    res['reason'] = f'Error: Get File size failed.  "{url}"  {e}'
                    raise e
                    return res

        if local_file_size != remote_file_size:
            res['success'] = False
            res['reason'] = f'Error: Remote File Size!=Local File Size.  "{url}" file size ' \
                            f'({remote_file_size}) <> known good file ("{local_file_path}") '\
                              'size ({local_file_size})'
            return res

        if hash_check:
            # download file
            if not downloaded_file:
                downloaded_file = page.save_page()
            if downloaded_file.exception:
                res['success'] = False
                res['reason'] = f'Error: Download Error. "{downloaded_file.filename}" from ' \
                                f'"{url}".  {downloaded_file.exception}'
                return res

            # hash check
            try:
                match = hash_match(downloaded_file.filename, local_file_path)
            except Exception as e:
                res['success'] = False
                res['reason'] = f'Error: Hash Error.  Unexpected failure of hash_match function' \
                                + f' of "{downloaded_file}" and ' \
                                + f'"{local_file_path}" modified ' + str(e)
                raise e
                return res

            if not match:
                res['success'] = False
                res['reason'] = f'Error: Get File Size Error.  Posted file ("{url}") and  ' \
                                + f'known good file ("{local_file_path}")' \
                                + f'are not the same.  Failed hash check.  ' \
                                + res['reason']
                return res

    if check_child_url:
        location = page.contains_child_url(child_url = check_child_url)
        if isinstance(location, Exception):
            res['success'] = False
            res['reason'] = f'Error: Get Timestamp Error.  Unable to get timestamp from ' \
                            f'"{url}". {check_child_url}'
            return res
        if not location:
            res['success'] = False
            res['reason'] = f'Error: Child Link not found Error.  "{url}" does not contain ' \
                            + f' a link to "{check_child_url}").  '
            return res

    # Check web page posted date
    if posted_after:
        res['reason'] += f'Warning: HTTP Timestamp not supported.  "{url}" is HTTP; file ' \
                         f'timestamp is not supported'
        # remote_file_date = page.timestamp()
        # if isinstance(remote_file_date, Exception):
        #     res['success'] = False
        #     res['reason'] = f'Error: unable to get timestamp from "{url}". {remote_file_date}'
        #     return res
        # elif page.timestamp() >= posted_after:
        #     res['success'] = False
        #     res['reason'] = f'Error: "{url}" posted after ' \
        #                     + '{dtdt.strftime(dtdt.now(), datetime_us_fmt)}'
        #     return res
        # res['timestamp'] = remote_file_date.isoformat()

    if res['success'] is None:
        res['success'] = True
    return res


@error_handler.wrap(on_error_return=[])
def deep_link_check_ftp(url, local_file_path = '',
                        hash_check: bool = True,
                        check_child_url: str = '',  # ignored
                        description = '',
                        posted_after: Union[dtdt, None] = None,
                        working_dir = Path()):
    # Initialize from arguments
    url = url.strip()
    local_file_path = local_file_path.strip()
    check_child_url = check_child_url.strip()
    description = description.strip()
    downloaded_file = None

    # Initialize result dict
    res = result_template.copy()
    res['description'] = description
    res['url'] = url
    res['child url'] = check_child_url
    res['orig file path'] = local_file_path

    try:
        ftp = FTP(url)
    except Exception as e:
        res['success'] = False
        res['reason'] = f'Error:  FTP Session Error.  Cannot create FTP session: FTP("{url}").'\
                        + str(e)
        raise e
        return res

    if posted_after:
        try:
            remote_file_date = ftp.modified(host_or_url = url)
        except Exception as e:
            res['success'] = False
            res['reason'] = f'Error: Get Modified Date Error.  Unable to get modified date of ' \
                            f'"{url}" from server.' + str(e)
            return res
            raise e
        res['timestamp'] = remote_file_date.isoformat()

        if remote_file_date >= posted_after:
            res['success'] = False
            res['reason'] = f'Error: Stale File Error.  "{url}" posted after ' \
                            + '{dtdt.strftime(dtdt.now(), datetime_us_fmt)}'
            return res

    if local_file_path:
        # check file size match
        try:
            local_file_size = Path(local_file_path).getsize()
        except OSError as e:
            res['success'] = False
            res['reason'] = f'Error: Open Local File Error.  ' \
                            f'toolbox.link_checker.deep_link_check_ftp() ' \
                            + f'cannot open local_file_path, "{local_file_path}".  ' \
                            + 'File probably does not exist' + str(e)
            return res
        except Exception as e:
            res['success'] = False
            res['reason'] = f'Error: Get Local File Size Error.  unable to get file ' \
                            f'size of known good file "{local_file_path}".' + str(e)
            raise e
            return res

        try:
            remote_file_size = ftp.size(host_or_url = url)
        except Exception as e:
            try:
                downloaded_file = ftp.download(url_or_path = url, overwrite = True,
                                               tgt_folder = working_dir)
                remote_file_size = downloaded_file.size
                # remote_file_size = Path(downloaded_file.target_filename).getsize()
            except FileNotFoundError as e:
                res['success'] = False
                res['reason'] = f'Error: File not found on FTP server: "{url}"' + str(e)
                return res
            except Exception as e:
                res['success'] = False
                res['reason'] = f'Error: Get FTP File Size unable to get file size of ' \
                                + f'"{url}" from server.' + str(e)
                raise e
                return res

        if local_file_size != remote_file_size:
            res['success'] = False
            res['reason'] = f'Error: File Sizes Different. ' \
                            + ' "{ftp.url}" file size ({remote_file_size}) ' \
                            + f'<> known good file ("{local_file_path}") ' \
                            + f'size ({local_file_size})'
            return res

        if hash_check:
            # download file
            if not downloaded_file:
                try:
                    downloaded_file = ftp.download(url_or_path = url, overwrite = True,
                                                   tgt_folder = working_dir)
                except Exception as e:
                    res['success'] = False
                    res['reason'] = f'Error: Download Error.  Unable to download ' \
                                    + f'"{url}" from server.' + str(e)
                    raise e
                    return res

            # hash check
            try:
                if not hash_match(downloaded_file.target_filename, local_file_path):
                    res['success'] = False
                    res['reason'] = f'Error: Hash Check failed.  Posted file ("{url}") and  ' \
                                    + f' known good file ("{local_file_path}") ' \
                                    + f' are not the same.  Failed hash check.  '
                    return res
            except Exception as e:
                res['success'] = False
                res['reason'] = f'Error: Unexpected Hash Check Error.  Failure attempting ' \
                                + f'to hash check "{url}" downloaded to ' \
                                + f'"{downloaded_file.target_filename}" against ' \
                                + '"{local_file_path}"' + str(e)
                raise e
                return res

    if check_child_url:
        res['reason'] += f'Warning: check_child_url ignored.  "{url}" is FTP; check_child_url ' \
                         f'argument is ignored.'

    res['success'] = True
    return res


def check_links_from_file(links_to_check_csv_or_df,
                          output_file: str = tb_cfg['LINK_CHECKER']['DEFAULT_LINKS_CSV'],
                          verbose: bool = True,
                          hash_check = True) -> pd.DataFrame:
    """
    Read in links from csv input_file.  For each link, run deep_link_check() and save
    results to csv output_file.
    :param links_to_check_csv_or_df: a csv file or pd.DataFrame containing columns:
                        description, url, orig_file, check_child_url, comment.
                        The input_file contains the following columns:
                            description: a description of the url
                            url: a webpage address
                            orig_file: the path of an known good copy of the file that should be
                                       found at url check_child_url: a link that should be found
                                       direclty on the page with address url comment: comment
                            check_child_url: after opening url as link_checker.WebPage,
                                             see if WebPage contains link check_child_url
                            comment: a string to include in the 'comments' column of output_file
    :param output_file: the name of the file in which to save the results. If not provided,
                        then the output is not written to a file.  if True and output_file
                        already exits, then output_file is overwritten.
    :param verbose: If True, print the results of each link check as completed.
    :param hash_check: if True and input_file contains an orig_file, then hash check will
                       be performed between input_file.orig file and input_file.orig file
    :return: pd.DataFrame containing one row containing results for each link checked
    Creates output_file (defined below) with results.
    Output file columns: are as per result_template dict defined above.
        row number: results are produced with row numbers 0, 1, 2, ... taken
                    from the index of the dataframe used herein.
        success: True/False: Did url load successfully?
        description: copy of description from input_file
        url: copy of url from input_file
        status: the http/ftp returned status of url
        reason: the http/ftp returned reason of url
        child url: copy of check_child_url from input_file
        child url status: the http/ftp returned status of check_child_url
        child url reason: the http/ftp returned reason of check_child_url
        child url header: the http/ftp returned header of check_child_url
        size on server: size of the file (if applicable) on the server.  Note
                        this is not expected to match the size of the orig_file
                        if check_child_url is an aspx page (i.e., the file is
                        wrapped).
        downloaded file size: if applicable, url is downloaded as a file, and
                              the size of that download file is returned here.
        orig file size: the size of the file on disk at path orig_file
        header: the http/ftp returned header of url

    """

    # input_df: pd.DataFrame = pd.DataFrame(columns = links_to_check_csv_columns)
    if type(links_to_check_csv_or_df) in [str, Path]:
        links_to_check_csv_or_df = Path(links_to_check_csv_or_df)
        if links_to_check_csv_or_df.parent.str == '.':  # no folder structure specified
            input_file = Path(DIR_HOME).joinpath(links_to_check_csv_or_df)
        # input_file -> DataFrame
        input_df = pd.read_csv(links_to_check_csv_or_df, delimiter = ',')
        assert (len(input_df.columns) == len(links_to_check_csv_columns))
        if type(input_df.columns) == pd.RangeIndex:
            input_df.columns = links_to_check_csv_columns
    elif type(links_to_check_csv_or_df) is pd.DataFrame:
        input_df = links_to_check_csv_or_df
    elif is_iterable(links_to_check_csv_or_df):
        input_df = pd.DataFrame(links_to_check_csv_or_df, columns = links_to_check_csv_columns)

    if 'contains_url' in input_df.columns:
        input_df.rename(columns = {'contains_url': 'check_child_url'}, inplace = True)
    assert (len(input_df.columns) == len(links_to_check_csv_columns))
    assert (all(input_df.columns == links_to_check_csv_columns))

    for col in ['description', 'url', 'orig_file', 'check_child_url', 'comment']:
        input_df[col] = input_df[col].astype(str).replace('nan', '')
        # input_df[col] = input_df[col].replace(None, '')

    res = []
    row_cnt = input_df.shape[0]
    fail_cnt = 0
    for index, row in input_df.iterrows():
        # collect input information from the input file.
        d = deep_link_check(url = row['url'],
                            local_file_path = row['orig_file'],
                            hash_check = hash_check,
                            check_child_url = row['check_child_url'],
                            description = row['description'])
        res.append(d)
        if not d['success']:
            fail_cnt += 1

        if verbose:
            prt_msg = f"\nFinished {index + 1} of {row_cnt}, {row['description']}: "
            print(prt_msg, d['url'])

            if not d['success']:
                print(f"    - Passed")
            else:
                print(f"    - Failed: {d['reason']}, {d['child url reason']}")

    # convert results to dataframe
    res = pd.DataFrame(res)
    # Rearrange columns: See result_template dict defined above.  All functions must use these
    # same columns.
    new_index = ['success', 'reason', 'description', 'url', 'request status', 'child url',
                 'child url status', 'child url reason', 'child url header',
                 'size on server', 'downloaded file size', 'orig file size', 'orig file path',
                 'timestamp', 'header']
    res = res.reindex(new_index, axis = "columns")
    # res = res.sort_values('description')

    if fail_cnt > 0:
        err_df = res.copy()
        err_df = err_df[err_df.success == False]
        err_df = err_df[['description', 'request status', 'reason',
                         'child url status', 'child url reason']]
        print('*' * 60, '\n')
        print(f'{fail_cnt} link check(s) failed\n')
        pprint(err_df[['description', 'reason']])
        print('*' * 60, '\n')

    # If output_file (an argument to this function) is provided, then save the results
    # to the out_put file.  Also, if output_file contains only the basename (file.ext,
    # not folder), then save to the default directory, DIR_OUT.
    if output_file:
        # save to file
        # if no folder provided in output_file name, then save to DIR_OUT
        if os.path.split(output_file)[0] == '':
            # no path provided
            output_file = Path(DIR_OUT).joinpath(output_file)
        backup_file(output_file)
        try:
            # write to file
            res.to_csv(output_file, index = False)
        except Exception as e:
            msg = f'Unable to save as "{output_file}". '
            # if we haven't already, insert timestamp into filename

    return res


def check_local_files(links_to_check_csv_or_df):
    pass


def process_links_to_check_csv_or_df(links_to_check_csv_or_df: Union[str, Path, pd.DataFrame,
                                                                     dict]) -> pd.DataFrame:
    # TODO: adopt use of thsi functions by check_links_from_file and check_local_files
    """
    converts links_to_check_csv_or_df to a pd.DataFrame and asserts that it has
    the correct columns.
    :param links_to_check_csv_or_df: some iterable that can be converted to a pd.DataFrame
                                     and has the expected columns.
    :return: pd.DataFrame to be consumed by check_links_from_file() or check_local_files()
    """
    # result: pd.DataFrame
    if type(links_to_check_csv_or_df) in [str, Path]:
        links_to_check_csv_or_df = Path(links_to_check_csv_or_df)
        if links_to_check_csv_or_df.parent.str == '.':  # no folder structure specified
            input_file = Path(DIR_HOME).joinpath(links_to_check_csv_or_df)
        # input_file -> DataFrame
        result = pd.read_csv(links_to_check_csv_or_df, delimiter = ',')
        assert (len(result.columns) == len(links_to_check_csv_columns))
        if type(result.columns) == pd.RangeIndex:
            result.columns = links_to_check_csv_columns
    elif type(links_to_check_csv_or_df) is pd.DataFrame:
        result = links_to_check_csv_or_df
    elif is_iterable(links_to_check_csv_or_df):
        result = pd.DataFrame(links_to_check_csv_or_df, columns = links_to_check_csv_columns)

    if 'contains_url' in result.columns:
        result.rename(columns = {'contains_url': 'check_child_url'}, inplace = True)
    assert (len(result.columns) == len(links_to_check_csv_columns))
    assert (all(result.columns == links_to_check_csv_columns))

    for col in ['description', 'url', 'orig_file', 'check_child_url', 'comment']:
        result[col] = result[col].astype(str).replace('nan', '')
        # result[col] = result[col].replace(None, '')
    return result


def main():
    # ##############################################################################
    # New config
    # ##############################################################################
    # cfg = tb_cfg  # Your personal config file for toolbox.
    global dir_home
    global default_config
    dir_home = Path(r"\\corp.pjm.com\shares\TransmissionServices\TSI\Compliance\OASISWebChecker"
                    r"\test")
    cfg = Config(file = dir_home.joinpath("link_checker.cfg"))
    default_config = {
        'LINK_CHECKER': {
            "HASH_CHECK": True,
            "OPEN_RESULTS": True,
            "VERBOSE": True,
            "DIR_HOME": dir_home.str,
            "DIR_IN": dir_home.joinpath("inputs").str,
            "DIR_OUT": dir_home.joinpath("outputs").str,
            "DEFAULT_LINKS_CSV": dir_home.joinpath("links_to_check.csv").str,
            "DEFAULT_RESULTS_CSV":
                dir_home.joinpath("outputs").joinpath("links_to_check_results.csv").str,
            "EXCLUDE_LINKS_STARTING_WITH": [""],
            }
        }
    cfg.update_if_none(dict_of_parameters = default_config, recurse = True)

    # ##############################################################################
    # Link Check
    # ##############################################################################
    backup_file(cfg['LINK_CHECKER']['DEFAULT_RESULTS_CSV'])
    df = check_links_from_file(links_to_check_csv_or_df = cfg['LINK_CHECKER']['DEFAULT_LINKS_CSV'],
                               output_file = cfg['LINK_CHECKER']['DEFAULT_RESULTS_CSV'],
                               verbose = cfg['LINK_CHECKER']['VERBOSE'],
                               hash_check = cfg['LINK_CHECKER']['HASH_CHECK'])

    print(f'\nConfiguration Settings ({cfg.file}):')
    for k, v in cfg['LINK_CHECKER'].items():
        print('   ', k.ljust(30, ' '), '  ', v)

    print('\n******  Results file:', cfg['LINK_CHECKER']['DEFAULT_RESULTS_CSV'], ' ******')

    # Open results of link_checker in default csv file viewer
    if cfg['LINK_CHECKER']['OPEN_RESULTS']:
        try:
            proc = subprocess.Popen(cfg['LINK_CHECKER']['DEFAULT_RESULTS_CSV'], shell=True,
                                    stdin=None, stdout=None, stderr=None, close_fds=True)
        except Exception as e:
            warn(f'Cannot open link_checker results. {e}')

if __name__ == '__main__':
    main()
