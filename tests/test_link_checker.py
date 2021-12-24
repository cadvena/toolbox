# -- 1 -- Import unittest (find 2 under "if __name__ == '__main__'")
import unittest
import requests
from toolbox import tb_cfg
from toolbox.config import Config
import toolbox.link_checker as lc
from toolbox.link_checker import WebPage, deep_link_check, deep_link_check_http, \
    deep_link_check_ftp  # , get_links_from_webpage
from configparser import ConfigParser  #
import time
from datetime import datetime as dtdt
import os
from toolbox.pathlib import Path
# import pandas as pd
# from pathlib.py import Path

# ##############################################################################
# Config
# ##############################################################################
dir_home = Path(r"\\corp.pjm.com\shares\TransmissionServices\TSI\Compliance\OASISWebChecker"
                r"\test")
cfg = Config(file = dir_home.joinpath("link_checker.cfg"))
default_config = {
    'LINK_CHECKER': {
        "HASH_CHECK": True,
        "OPEN_RESULTS": True,
        "VERBOSE": True,
        "DIR_HOME": str(dir_home),
        "DIR_IN": dir_home.joinpath("inputs").str,
        "DIR_OUT": dir_home.joinpath("outputs").str,
        "DEFAULT_LINKS_CSV": dir_home.joinpath("links_to_check.csv").str,
        "DEFAULT_RESULTS_CSV":
            dir_home.joinpath("outputs").joinpath("links_to_check_results.csv").str,
        "EXCLUDE_LINKS_STARTING_WITH": [""],
        }
    }
cfg.update_if_none(dict_of_parameters = default_config, recurse = True)

# if 'TEST_WEB_CRAWLER_INI' in tb_cfg.keys():
#     ini_file = Path(tb_cfg['TEST_WEB_CRAWLER_INI'])
# else:
#     ini_file = Path('.').joinpath('web_crawler.ini')
#     if not ini_file.exists():
#         ini_file = Path(tb_cfg['WEB_CRAWLER_INI'])

for fp in [cfg['LINK_CHECKER']['DIR_HOME'], cfg['LINK_CHECKER']['DIR_IN'],
           cfg['LINK_CHECKER']['DIR_OUT']]:
    fp = Path(fp)
    if not fp.exists():
        fp.mkdir(parents = True)

# -- 3 -- Write 'Test...' class and 'test_...' methods.
# Begin test classes with "Test"


class TestIni(unittest.TestCase):
    start = None
    stop = None
    def setup(self):
        self.start = time.time()
        print(r"Calling TestWebPage.tearDown() @ ", self.stop,
              'Run time:', self.stop - self.start)

    def tearDown(self):
        print('')
        self.stop = time.time()
        print(r"Calling TestWebPage.tearDown() @ ", self.stop)

    def test_ini(self):
        self.ini = ConfigParser()
        if os.path.exists('test.ini'):
            os.remove('test.ini')
        self.ini.read('test.ini')
        self.assertEqual(['DEFAULT'], [x for x in self.ini.keys()])
        keys = [x for x in self.ini.keys()]
        self.assertFalse('MICKEY' in keys)
        self.assertTrue(len(keys) == 1)
        # TODO: needs much mroe exhaustive test script.

    def test_ini_default(self):
        # TODO
        pass

    def test_ini_default_boolean(self):
        # TODO
        pass


class TestWebPage(unittest.TestCase):
    oasis = "https://www.pjm.com/markets-and-operations/etools/oasis.aspx"
    start = None
    stop = None
    def setup(self):
        self.start = time.time()
        print(r"Calling TestWebPage.setUp() @ ", self.start)

    def tearDown(self):
        print('')
        self.stop = time.time()
        print(r"Calling TestWebPage.tearDown() @ ", self.stop)

    def test_domain(self):
        self.assertEqual(('pjm', 'com'), lc.domain('http://www.pjm.com'))
        self.assertEqual(('pjm', 'com'), lc.domain('www.pjm.com'))
        self.assertEqual(('pjm', 'com'), lc.domain('pjm.com'))
        self.assertEqual(('pjm', ), lc.domain('pjm'))
        self.assertEqual(('', ), lc.domain(''))
        with self.assertRaisesRegexp(TypeError, 'not iterable'):
            lc.domain(None)

    def test_clean_url(self):
        self.assertEqual('asdf', lc.clean_url('  asdf '))
        self.assertEqual('www.pjm.com', lc.clean_url('www.pjm.com/'))
        self.assertEqual('https://www.pjm.com/oasis', lc.clean_url('https://www.pjm.com/oasis/'))

    def test_webpage_init(self):
        url = 'www.pjm.com'
        page = WebPage(url)
        self.assertTrue(page.cache)
        expect = 'http://www.pjm.com'
        self.assertEqual(expect, page.url, f'expected {expect}, got {page.url}')
        page = WebPage('http://pjm.com/')
        self.assertTrue(page.ok())
        self.assertEqual('http://pjm.com', page.url)
        self.assertEqual('pjm.com', page.internal_domain)

    def test_webpage_head(self):
        page = WebPage('https://not.a.real.website.com/')
        h = page.head()
        self.assertTrue(isinstance(page.exceptions.head_exception, Exception))
        self.assertTrue(isinstance(page.ok(), Exception))

        url = self.oasis
        page = WebPage(url)
        h = page.head()
        self.assertFalse(isinstance(h, Exception))
        self.assertTrue(page.ok())

    def test_webpage_get(self):
        url = self.oasis
        page = WebPage(url)
        self.assertTrue(page.cache)
        self.assertTrue(page.ok())
        self.assertTrue(page.find('NAESB Home Page') > 0)
        self.assertEqual(url, page.url)
        h = page.head()
        self.assertEqual(None, page.exceptions.head_exception)
        h2 = requests.head(url)
        self.assertEqual(url, h.url)
        self.assertEqual(str(h2), str(h))
        r = page.get()
        r2 = requests.get(url)
        self.assertEqual(str(r2), str(r))
        self.assertEqual(None, page.exceptions.get_exception)

    def test_webpage_ok(self):
        url = self.oasis
        page = WebPage(url, cache = False)
        response = page.get()
        self.assertEqual('\r\n\r\n<!DOCTYPE html>\r', response.text[:20])
        page._get = 123
        self.assertEqual(123, page._get)
        with self.assertRaisesRegexp(AttributeError, "has no attribute 'text'"):
            page._get.text

        # # TODO: This is case is not expected, but whoudl be made to work
        # response = page.get()
        # self.assertEqual(123, page._get)

        url = 'http://not.a.real.website.com'
        page = WebPage(url)

        # get, head, expected
        test_list = [
            [False, False, False],
            [True, True, True],
            [True, False, False],
            [False, True, False],
            [False, None, False],
            [None, False, False],
            [True, None, True],
            [None, True, True],
            ]
        for g, h, expect in test_list:
            page._get_exception = g
            page._head_exception = h
            ok = page.ok()
            self.assertEqual(expect, ok, f'WebPage.ok({g},{h}) = {ok}, but should be {expect}')

    def test_webpage_find(self):
        url = self.oasis
        page = WebPage(url, cache = False)
        result = page.find("NAESB")
        self.assertTrue(result > 0, "Expected to find 'NAESB' on the oasis homepage")
        result = page.find("Hitler")
        self.assertTrue(result == -1, "Did not expect to find 'Hitler' on the oasis homepage")
        result = page.find("https://www.pjm.com/-/media/etools/capacity-exchange/erpm-designated.ashx")
        self.assertTrue(result)

    def test_webpage_timestamp(self):
        url = self.oasis
        page = WebPage(url, cache = False)
        result = page.timestamp()
        self.assertTrue(isinstance(result, dtdt))

    def test_webpage_contains_child_url(self):
        url = self.oasis
        page = WebPage(url, cache = False)
        result = page.contains_child_url('http://www.naesb.org/')
        self.assertTrue(result)
        result = page.contains_child_url('http://not.a.real.website.com')
        self.assertFalse(result)
        result = page.contains_child_url('NAESB')
        self.assertFalse(result)

    def test_webpage_anchors(self):
        url = self.oasis
        page = WebPage(url)
        anchors = page.anchors(cache = False, full_links = False,
                               same_domain = False, regex_pattern = None)
        self.assertTrue('http://dataminer2.pjm.com/list' in anchors)

        # TODO: WebPage.anchors() is not getting every link.  For instance,
        # it is missing these:
            # "https://www.pjm.com/-/media/etools/capacity-exchange/erpm-designated.ashx"
            # "http://www.naesb.org"
        for anchor in anchors:
            if lc.clean_url(anchor) == "https://www.pjm.com/-/media/etools/capacity-exchange/erpm-designated.ashx":
                return True
        for anchor in anchors:
            if lc.clean_url(anchor).endswith("http://www.naesb.org"):
                return True

    def test_webpage_text(self):
        url = self.oasis
        page = WebPage(url)
        text = page.text()
        result = text.find("PJM")
        self.assertTrue(result > -1)
        result = text.find("NAESB")
        self.assertTrue(result > -1)
        result = text.find("All chocolate is purple.")
        self.assertTrue(result == -1)
        page._text = 'blue'
        page.text()
        result = text.find("PJM")
        self.assertFalse(result == -1)


class TestDeepLinkCheckHTTP(unittest.TestCase):
    oasis = "https://www.pjm.com/markets-and-operations/etools/oasis.aspx"
    start = None
    stop = None
    def setup(self):
        self.start = time.time()
        print(r"Calling TestWebPage.setUp() @ ", self.start)

    def tearDown(self):
        print('')
        self.stop = time.time()
        print(r"Calling TestWebPage.tearDown() @ ", self.stop)

    def test_deep_link_check_http(self):
        # Test argument: contains_url
        url = self.oasis
        result = deep_link_check_http(url, check_child_url = "http://www.naesb.org")
        self.assertTrue(result)
        result = deep_link_check_http(url, check_child_url = "www.naesb.org")
        self.assertTrue(result)
        result = deep_link_check_http(url, check_child_url = "http://nowhere.not_real.bob")
        self.assertFalse(result['success'])
        self.assertEqual(url, result['url'])
        self.assertEqual(200, result['request status'])
        self.assertTrue(result['reason'].startswith('Error'))

        url = 'https://www.pjm.com/pub/oasis/ATCID.pdf'
        known_good = r"\\corp.pjm.com\shares\TransmissionServices\TSI\Compliance\OASISWebChecker" \
                   r"\inputs\ATCID.pdf"
        result = deep_link_check_http(url, local_file_path = known_good, hash_check = False)
        self.assertTrue(result)
        result = deep_link_check_http(url, local_file_path = known_good, hash_check = True)
        self.assertTrue(result)

        # TODO: These don't pass.  Uncomment and fix the code in link_checker.py
        # known_good = r"\\corp.pjm.com\shares\TransmissionServices\TSI\Compliance\OASISWebChecker" \
        #            r"\inputs\CBMID.pdf"
        # result = deep_link_check_http(url, local_file_path = known_good, hash_check = False)
        # self.assertFalse(result)
        # result = deep_link_check_http(url, local_file_path = known_good, hash_check = True)
        # self.assertFalse(result)

    def test_deep_link_check_ftp(self):
        url = 'ftp://ftp.pjm.com/oasis/ATCID.pdf'
        known_good = r"\\corp.pjm.com\shares\TransmissionServices\TSI\Compliance\OASISWebChecker" \
                     r"\inputs\ATCID.pdf"
        result = deep_link_check_ftp(url = url, local_file_path = known_good, hash_check = False)
        self.assertTrue(result)
        result = deep_link_check_ftp(url = url, local_file_path = known_good, hash_check = True)
        self.assertTrue(result)

        # TODO: These don't pass.  Uncomment and fix the code in link_checker.py
        # known_good = r"\\corp.pjm.com\shares\TransmissionServices\TSI\Compliance\OASISWebChecker" \
        #              r"\inputs\CBMID.pdf"
        # result = deep_link_check_ftp(url = url, local_file_path = known_good, hash_check = False)
        # self.assertFalse(result)
        # result = deep_link_check_ftp(url = url, local_file_path = known_good, hash_check = True)
        # self.assertFalse(result)

        d = dtdt(year = dtdt.now().year -30, month = 12, day=31)
        result = deep_link_check_ftp(url = url, posted_after = d)
        self.assertTrue(result)
        d = dtdt(year = dtdt.now().year + 10, month = 12, day=31)
        # TODO: This does not pass.  Uncomment and fix the code in link_checker.py
        # result = deep_link_check_ftp(url = url, posted_after = d)
        # self.assertFalse(result)


class TestCheckLinksFromFile(unittest.TestCase):
    """
    Tests the deep_link_check function.

    Test scenarios:
        links_to_check.csv:
            - malformed filename
            - file does not exist
            - file is not a text document
            - different number of columns on different lines
            - extra columns
            - too few columns
            - wrong column names
            - empy rows
            - header (column names)
            - no header
            - contains characters that URLs don't like
            - contains characters that csv files don't like
        url:
            - good pjm url
            - good pjm http
            - good pjm https
            - good non-pjm url
            - malformed pjm-like url (http)
            - url that returns 500
            - url that returns 400
            - redirect url (302)
            - good pjm ftp
            - good pjm ftps
            - bad ftp
            - bad ftps
            - non-pjm ftp
            - non-pjm ftps
            - malformed pjm-like ftp
        description:
            - with CRLF
            - with unusual characters that might break csv parsing
        child_url:
            Is only valid for http(s), ignored for ftp
            - exists on parent page (url)
            - does not exist on parent page
            - child_url stored as a relative path in web page (url)
            - child_url is a relative webpage in links_to_check.csv
            - good child_url http
            - good https
            - bad http
            - bad https
            - malformed http
            - non-pjm http
            - non-pjm https
            - pjm ftp
            - pjm ftps
            - non-pjm ftp
            - non-pjm ftps
            - malformed ftp
            - malformed ftps
            - is empty file
            - contains characters unfriendly to csv
            - contains characters unfriendly to http
            - contains characters unfriendly to ftp
            - ftp requires login
            - ftp requires proxy
        orig file
            - pass dir name instead of filename
            - malformed filename
            - empty file
            - well formed filename, but file not exist
            - ftp address (not expected)
            - http address (not expected)
            - UNC name starging with "\\corp"
            - filename starting with "C:\"
            - relative filename
            - file not exist
            - cannot open/read due to permissions error
        File comparison
            File size
                - same file size
                - url not found
                - local file not found
                - different file sizes
                - one file empty
                - both files empty
            Modified data
                Note: http files do not have modified dates (on the server).  ftp files do. code should ignore this check if url is http(s)
                - equal
                - not equal
            Hash (identical cantent check)
                - Same file size; different hash
        output file
            - output file is locked (e.g. open for write/edit by another application
            - parent folder of file does not exist
            - malformed filename
            - file exists (expect it to be automatically backed up and overwritten)
            - try an unusual extension that Windows doesn't know how to open (no default application assigned)
            - is read-only
    """

    oasis = "https://www.pjm.com/markets-and-operations/etools/oasis.aspx"
    start = None
    stop = None
    def setup(self):
        self.start = time.time()
        print(r"Calling TestWebPage.setUp() @ ", self.start)

    def tearDown(self):
        print('')
        self.stop = time.time()
        print(r"Calling TestWebPage.tearDown() @ ", self.stop)

    def test_deep_link_check_http(self):
        # TODO: write the test script.
        pass


class TestMain(unittest.TestCase):
    start = None
    stop = None
    def setup(self):
        self.start = time.time()
        print(r"Calling TestWebPage.setUp() @ ", self.start)

    def tearDown(self):
        print('')
        self.stop = time.time()
        print(r"Calling TestWebPage.tearDown() @ ", self.stop)

    def test_main(self):
        input_file = cfg['LINK_CHECKER']['DEFAULT_LINKS_CSV']
        output_file = cfg['LINK_CHECKER']['DEFAULT_RESULTS_CSV']
        results_df = lc.main()
        print(results_df)
        print('\nResults file:', output_file)

if __name__ == '__main__':
    # -- 2 -- invoke the framework --
    # invoke the unittest framework
    # unittest.main() will capture all fo the tests
    # and run them 1-by-1.
    unittest.main()
