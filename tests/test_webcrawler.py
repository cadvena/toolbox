# -- 1 -- Import unittest (find 2 under "if __name__ == '__main__'")
# import unittest is required
import unittest
# import the module being tested
from toolbox.web_crawler import deep_link_check, webpage_contains_url, \
    get_links_from_webpage, broken_link_finder, check_links_from_file, examples
# from toolbox.swiss_army import make_iterable
# other imports
from configparser import ConfigParser  #
import time
import os
import pandas as pd
from pathlib import Path

CONFIG_FILE = 'web_crawler.ini'
if not os.path.exists(CONFIG_FILE):
    # CONFIG_FILE does not exist in the tests folder, so get it directly from the toolbox folder.
    CONFIG_FILE = Path(__file__).parent.parent.joinpath('toolbox', 'web_crawler.ini')
assert(os.path.exists(CONFIG_FILE))
cfg = ConfigParser()
cfg.read(CONFIG_FILE)
assert(len(cfg._sections)>=1)
DIR_HOME = os.path.join(cfg['CHECK_LINKS_FROM_FILE']['DIR_HOME'], 'test')
DIR_IN = cfg['CHECK_LINKS_FROM_FILE']['DIR_IN']
DIR_OUT = cfg['CHECK_LINKS_FROM_FILE']['DIR_OUT']
# DIR_IN = os.path.join(DIR_HOME, 'inputs')
# DIR_OUT = os.path.join(DIR_HOME, 'outputs')
LINKS_CSV = cfg['CHECK_LINKS_FROM_FILE']['DEFAULT_LINKS_CSV']
RESULTS_CSV = cfg['CHECK_LINKS_FROM_FILE']['DEFAULT_RESULTS_CSV']
RUN_CHECK_LINKS_FROM_FILE = cfg.getboolean(section= 'RUN', option = 'RUN_CHECK_LINKS_FROM_FILE')
RUN_EXAMPLES = cfg.getboolean(section='RUN', option = 'RUN_EXAMPLES')
RUN_CHECK_LINKS_ON_PAGES = cfg.getboolean(section= 'RUN', option = 'RUN_BROKEN_LINK_FINDER')
DEFAULT_CSV_VIEWER = cfg['DEFAULT']['DEFAULT_CSV_VIEWER']
HASH_CHECK = cfg['CHECK_LINKS_FROM_FILE']['HASH_CHECK']
LINKS_PAGES = cfg['BROKEN_LINKS_FINDER']['CHECK_LINKS_ON'].split(',')

for s in [DIR_HOME, DIR_IN, DIR_OUT]:
    if not os.path.exists(s):
        os.mkdir(s)

# -- 3 -- Write 'Test...' class and 'test_...' methods.
# Begin test classes with "Test"
class TestWebCrawler(unittest.TestCase):
    def setUp(self):
        print('')
        self.start = time.time()
        print(r"Calling .setUp() @ ", self.start)
        for d in [DIR_HOME, DIR_IN, DIR_OUT]:
            if not os.path.exists (s):
                os.mkdir (d)

        self.result_csv = os.path.join(DIR_OUT, 'test_result.csv')
        self.compliance_inputs_csv = ('compliance_inputs.csv')

        self.compliance_inputs_content = r"""
description,url,orig_file,contains_url,comment
OASIS Home Page contains link to NAESB homepage,https://www.pjm.com/markets-and-operations/etools/oasis,,http://www.naesb.org/,pjm.com landing page for oasis
oasis user guide,https://www.pjm.com/-/media/etools/oasis/oasis-user-guide.ashx,C:\temp\oasis-user-guide-orig.pdf,,
Study metrics 2020 q4,https://www.pjm.com/-/media/etools/oasis/20210105-quarterly-metrics-2020-q4.ashx,20210105-quarterly-metrics-2020-q4.pdf,,
Designated Network Resources,https://www.pjm.com/-/media/etools/capacity-exchange/erpm-designated.ashx,,,
"""
        with open(self.compliance_inputs_csv, 'w') as f:
            f.write(self.compliance_inputs_content)

        self.oasis_url = 'https://www.pjm.com/markets-and-operations/etools/oasis.aspx'

    def tearDown(self):
        print('')
        self.stop = time.time()
        print(r"Calling .tearDown() @ ", self.stop)
        if False:
            os.remove(self.compliance_inputs_csv)
            os.remove(self.result_csv)

    # -- 3.1 -- test cases
    # begin test methods with "test_"


    def test_get_links_from_webpage(self):
        # def get_links_from_webpage(url: str,
        #                            full_links: bool = True,
        #                            separate_foreign: bool = False) -> dict:
        # returns a dictionary of one or two sets of urls.

        # Create a tuple of combination of get_links_from_webpage() arguments.
        test_in = (
                   (self.oasis_url, True, True),
                   (self.oasis_url, True, False),
                   (self.oasis_url, False, True),
                   (self.oasis_url, False, False)
                   )

        for t in test_in:
            result = get_links_from_webpage(url=t[0], full_links = t[1], separate_foreign = t[2])
            # Confirm the correct keys are returned
            if t[2]:    # if separate_foreign
                # separate_foreign = True, so there should be 2 dict items in result
                self.assertEqual(len(result.keys()), 2)
                self.assertFalse('urls' in result.keys())
                self.assertTrue('local_urls' in result.keys())
                self.assertTrue('foreign_urls' in result.keys())
                pass
            else:
                # separate_foreign = False, so there should be 1 dict items in result
                self.assertEqual(len(result.keys()), 1)
                self.assertTrue('urls' in result.keys())
                self.assertFalse('local_urls' in result.keys())
                self.assertFalse('foreign_urls' in result.keys())
                pass
            if t[1]:  # if full_links
                # full_links = True (return absolute paths, not relative paths)
                for k in result.keys():
                    for lnk in result[k]:
                        # test that url starts with a valid prefix
                        valid_prefix = lnk[:4] in ['http', 'ftp:', 'ftps']
                        msg = f'full link test must start with http or ftp: {lnk[:12]}'
                        self.assertTrue(valid_prefix, msg)

        result = get_links_from_webpage(
                    url = 'https://www.pjm.com/markets-and-operations/etools/oasis.aspx',
                    full_links = True,
                    separate_foreign = False,
                    exclude_prefixes = ['mailto'])
        links = result['urls']
        for link in links:
            if link.startswith('mailto'):
                self.assertFalse(link.startswith('mailto'))
                continue


    def test_webpage_contains_url(self):
        # TODO: add tests for ftp, email an other url forms
        # dict of parent urls that DO contain the child url
        true_list = \
            [['https://www.pjm.com/markets-and-operations/etools/oasis.aspx',
              "https://www.pjm.com/markets-and-operations/etools/oasis/merch-trans-facilities"],
             ['https://www.pjm.com/markets-and-operations/etools/oasis.aspx',
              'https://tools.pjm.com/'],
             ['https://www.pjm.com/markets-and-operations/etools/oasis.aspx',
              'https://www.pjm.com/markets-and-operations/etools/oasis/atc-information.aspx'],
             ['https://www.pjm.com/markets-and-operations/etools/oasis.aspx',
              'http://www.naesb.org/'],
             ['https://www.pjm.com/markets-and-operations/etools/oasis.aspx',
              'https://www.pjm.com/-/media/etools/oasis/regional-practices-clean-pdf.ashx']
             ]
        # print('test_webpage_contains_url: true_list:')
        for item in true_list:
            # print('    item[0] contains item[1]: ', webpage_contains_url(item[0], item[1]))
            if not webpage_contains_url(item[0], item[1]):
                b = webpage_contains_url(item[0], item[1])
            self.assertTrue(webpage_contains_url(item[0], item[1]), f'{item[0]} does NOT '
                                                                     f'contain {item[1]}')

        # dict of parent urls that do NOT contain the child url
        false_list = \
            [['https://www.pjm.com/markets-and-operations/etools/oasis.aspx', 'not_a_link'],
             ['', ''],
             ['not_a_link', 'not_a_link'],
             [None, None],
             [None, 'https://www.pjm.com/markets-and-operations/etools/oasis.aspx'],
             ['', 'https://www.pjm.com/markets-and-operations/etools/oasis.aspx'],
             ['https://www.pjm.com/markets-and-operations/etools/oasis.aspx', None],
             ['not_a_link', None],
             ['not_a_link', 'http://www.pjm.com']
             ]
        for item in false_list:
            if webpage_contains_url(item[0], item[1]):
                b = webpage_contains_url(item[0], item[1])
            self.assertFalse(webpage_contains_url(item[0], item[1]), f'{item[0]} '
                                                                     f'contains {item[1]}')

    def test_deep_link_check(self):
        # self.result_csv set in SetUp()
        # self.config_csv set in SetUp()
        # result_csv = os.path.join(DIR_OUT, 'test_check_link_result.csv')
        # config_csv = os.path.join(DIR_OUT, 'test_check_link_cfg.csv')
        config_df = pd.read_csv(self.compliance_inputs_csv, delimiter = ',')

        res = []
        for index, row in config_df.iterrows():
            for s in ['description', 'url', 'orig_file', 'contains_url', 'comment']:
                if not isinstance(row[s], str):
                    row[s] = ''
            d = deep_link_check(url=row['url'],
                              local_file_path = row['orig_file'],
                              hash_check = True,
                              contains_url = row['contains_url'])
            res.append(d)

        # def check_link(url, local_file_path = None, hash_check: bool = True,
        #                contains_url: str = '', description = ''):
        # convert to dataframe
        res = pd.DataFrame(res)
        res.to_csv(self.result_csv)
        pass

    def test_check_links_from_file(self):
        check_links_from_file(input_file = LINKS_CSV,
                              output_file = RESULTS_CSV,
                              viewer = 'excel.exe',
                              open_results_when_done = True,
                              print_each = True)

    def test_examples(self):
        pass
        # examples()

    def test_broken_link_finder(self):
        broken_link_finder(urls = LINKS_PAGES[0],
                           print_to_console = True,
                           file_out = os.path.join(DIR_OUT,
                                                   'check_links_on_pages_output'),
                           viewer = 'excel.exe',
                           open_results_when_done = False)


if __name__ == '__main__':
    # -- 2 -- invoke the framework --
    # invoke the unittest framework
    # unittest.main() will capture all fo the tests
    # and run them 1-by-1.
    unittest.main()
