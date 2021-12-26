# 1 - Import unittest (find 2 under "if __name__ == '__main__'")
import unittest
from datetime import datetime as dtdt
from toolbox.file_util import ez_ftp
from toolbox.file_util.ez_ftp import StatsTuple, GetTuple, FTPPathParts, url_join

# StatsTuple = namedtuple (typename = 'StatsTuple',
#                          field_names = ('scheme', 'netloc', 'path', 'dirname',
#                                         'basename', 'modified', 'size')
#                         )
# FTPPathParts = namedtuple('FTPPathParts',['scheme', 'netloc', 'path',
#                                           'dirname', 'basename', 'url'])
# GetTuple = namedtuple (typename = 'GetTuple',
#                        field_names = ('scheme', 'netloc', 'path', 'dirname',
#                                       'basename', 'modified', 'size',
#                                       'target_filename')
#                        )

cbm = StatsTuple('ftp', 'ftp.pjm.com', '/oasis/CBMID.pdf', '/oasis',
                 'CBMID.pdf', dtdt(year = 2021, month = 12, day = 10,
                                   hour = 13, minute = 47, second = 28),
                 160160)
cbm_url = url_join(cbm.scheme, cbm.netloc, cbm.path)


class TestFTP(unittest.TestCase):
    def setUp(self):
        print('')
        print(r"Calling TestEzFTP.setUp()...")
        self.host_url_list = [['ftp://ftp.pjm.com/oasis/CBMID.pdf', 'ftp', 'ftp.pjm.com',
                          '/oasis/CBMID.pdf', 'oasis', 'CBMID.pdf',
                          'ftp://ftp.pjm.com/oasis/CBMID.pdf'],
                         ['FTP://ftp.pjm.com/oasis/', 'FTP', 'ftp.pjm.com',
                          '/oasis/', '/oasis', '', 'FTP://ftp.pjm.com/oasis/'],
                         ['ftp://ftp.pjm.com/oasis', 'ftp', 'ftp.pjm.com',
                          '/oasis', '/oasis', '', 'ftp://ftp.pjm.com/oasis'],
                         ['ftp://ftp.pjm.com/', 'ftp', 'ftp.pjm.com',
                          '/', '', '', 'ftp://ftp.pjm.com'],
                         ['ftp.pjm.com', 'ftp', 'ftp.pjm.com',
                          '', '', '', 'ftp://ftp.pjm.com']
                        ]
        # if os.path.exists(self.key_filename):
        #     os.remove(self.key_filename)

    def tearDown(self):
        print('')
        print(r"Calling .tearDown()...")

    def test_FTP(self):
        """
        Test the FTP class
        """
        # Instantiate ftp object from class
        ftp = ez_ftp.FTP(host_or_url='ftp.pjm.com')
        ftp.session()
        ftp.quit ()

    def test_url_split(self):
        x = ez_ftp.FTP.url_split('ftp://ftp.pjm.com/oasis/CBMID.pdf')
        self.assertEqual(x.path, '/oasis/CBMID.pdf')
        self.assertEqual(x.scheme, 'ftp')
        self.assertEqual(x.dirname, '/oasis')
        self.assertEqual(x.netloc, 'ftp.pjm.com')
        self.assertEqual(x.url, 'ftp://ftp.pjm.com/oasis/CBMID.pdf')
        self.assertEqual(x.basename, 'CBMID.pdf')

    def test_url_join(self):
        self.assertEqual(ez_ftp.FTP.url_join('ftp',cbm.netloc,'oasis'),
                         'ftp://ftp.pjm.com/oasis')
        self.assertEqual(ez_ftp.FTP.url_join('ftp',cbm.netloc, ''), 'ftp://ftp.pjm.com')
        self.assertEqual(ez_ftp.FTP.url_join('ftp',cbm.netloc), 'ftp://ftp.pjm.com')
        self.assertEqual(ez_ftp.FTP.url_join('',cbm.netloc), 'ftp://ftp.pjm.com')
        self.assertEqual(ez_ftp.FTP.url_join('',cbm.netloc,'/oasis/'), 'ftp://ftp.pjm.com/oasis/')
        self.assertEqual(ez_ftp.FTP.url_join('FTPS',cbm.netloc,'/oasis'), 'FTPS://ftp.pjm.com/oasis')

    def test_dirname(self):
        x = ez_ftp.FTP().dirname('ftp://ftp.pjm.com/parent/child/file.ext')
        self.assertEqual(x, '/parent/child')
        self.assertEqual(ez_ftp.FTP().dirname(cbm_url), cbm.dirname)
        self.assertEqual(ez_ftp.FTP().dirname('ftp://ftp.pjm.com/oasis/'), '/oasis')
        self.assertEqual(ez_ftp.FTP().dirname('ftp://ftp.pjm.com/oasis'), '/oasis')

    def test_modified(self):
        x = ez_ftp.FTP().modified(cbm_url)
        self.assertTrue(isinstance(x, dtdt))
        # self.assertEqual(x, cbm.modified)

    def test_size(self):
        x = ez_ftp.FTP().size(cbm_url)
        self.assertTrue(x > 100000)
        # self.assertEqual(x, cbm.size)

    def test_url(self):
        # inner list [host_or_url, scheme, netloc,
        #             path, dirname, basename, url]
        host_url_list = self.host_url_list

        # Setting host_or_url should set other parameters
        for x in host_url_list:
            ftp = ez_ftp.FTP(x[0])
            self.assertEqual(ftp.scheme.lower(), x[1].lower(), f'Scheme error. x = {x}')
            self.assertEqual(ftp.host, x[2], f'Host error. x = {x}')
            self.assertEqual(ftp.path, x[3], f'Path error. x = {x}')
            self.assertEqual(ftp.url.lower(), x[6].lower(), f'Url error. x = {x}')
            ftp.quit()

        # Setting FTP.url should correctly set other parameters
        for x in host_url_list:
            ftp = ez_ftp.FTP()
            ftp.url = x[6]
            self.assertEqual(ftp.scheme.lower(), x[1].lower(), f'scheme error. x = {x}')
            self.assertEqual(ftp.host, x[2], f'host error. x = {x}')
            self.assertEqual(ftp.path.lower().rstrip('/'), x[3].lower().rstrip('/'), f'path error. x = {x}')
            self.assertEqual(ftp.url.lower(), x[6].lower(), f'url error. x = {x}')
            # ftp.quit()

    def test_session(self):
        # FTP.session() # equivalent to FTP.connect() + FTP.login()
        ftp = ez_ftp.FTP()
        ftp.session('ftp.pjm.com')
        ftp.quit ()

    def test_download(self):
        ftp = ez_ftp.FTP(host_or_url='ftp.pjm.com')
        ftp.download(cbm_url, tgt_folder = 'c:/temp')
        ftp.download(cbm.netloc + cbm.path, tgt_folder = 'c:/temp')

    def test_stats(self):
        stats = ez_ftp.stats('ftp://ftp.pjm.com/oasis/CBMID.pdf')
        self.assertEqual(stats.scheme, 'ftp', f'scheme should be "ftp", but is "{stats.scheme}"')
        self.assertEqual(stats.netloc, 'ftp.pjm.com',
                         f'netloc should be "ftp.pjm.com", but is "{stats.netloc}"')
        self.assertEqual(stats.path, '/oasis/CBMID.pdf',
                         f'path should be "/oasis/CBMID.pdf", but is "{stats.path}"')
        self.assertEqual(stats.dirname, '/oasis',
                         f'dirname should be "/oasis", but is "{stats.dirname}"')
        self.assertEqual(stats.basename, 'CBMID.pdf',
                         f'basename should be "CBMID.pdf, but is "{stats.basename}"')
        self.assertTrue(stats.modified > dtdt(year=2021, month = 1, day = 20,
                                              hour = 14, minute = 56, second = 15),
                         f'modified should be 2021-01-20 14:56:15, but is {stats.modified}')
        self.assertEqual(stats.size, 160160,
                         f'size should be 177706, but is "{stats.size}"')


        host_url_list = self.host_url_list
        # FTP.stats
        x = host_url_list[1] # 'FTP://ftp.pjm.com/oasis/'  #
        ftp = ez_ftp.FTP(x[0])
        self.assertTrue(ftp.exists(x[6]))
        stats = ftp.stats(x[6])
        ftp.quit()
        # stats field_names = ('scheme', 'netloc', 'path', 'dirname',
        #                      'basename', 'modified', 'size')
        self.assertEqual(stats.scheme.lower().strip('/'), x[1].lower().strip('/'))
        self.assertEqual(stats.netloc.lower().strip('/'), x[2].lower().strip('/'))
        self.assertEqual(stats.path.lower().strip('/'), x[3].lower().strip('/'))
        self.assertEqual(stats.dirname.lower().strip('/'), x[4].lower().strip('/'))
        self.assertEqual(stats.basename.lower().strip('/'), x[5].lower().strip('/'))
        self.assertTrue(isinstance(stats.modified, type(None)))
        # self.assertTrue(isinstance(stats.modified, dtdt))
        self.assertEqual(stats.size, None)

    def test_exists(self):
        # FTP.exists()
        ftp = ez_ftp.FTP('ftp.pjm.com')
        ftp.session()
        self.assertTrue(ftp.exists('ftp://ftp.pjm.com/oasis/CBMID.pdf'))
        self.assertTrue(ftp.exists('ftp://ftp.pjm.com/oasis'))
        self.assertTrue(ftp.exists('ftp://ftp.pjm.com/oasis/'))
        self.assertTrue(ftp.exists('/oasis/'))
        self.assertTrue(ftp.exists('/oasis'))
        self.assertTrue(ftp.exists('/oasis/CBMID.pdf'))
        self.assertTrue(ftp.exists('oasis/CBMID.pdf'))
        self.assertTrue(ftp.exists('CBMID.pdf'))
        ftp.cwd('oasis')
        self.assertTrue(ftp.exists('CBMID.pdf'))
        ftp.quit ()

    def test_is_dir(self):
        # FTP.is_dir()
        ftp = ez_ftp.FTP ('ftp.pjm.com')
        ftp.session()
        self.assertFalse(ftp.is_dir('ftp://ftp.pjm.com/oasis/CBMID.pdf'))
        self.assertTrue(ftp.is_dir('ftp://ftp.pjm.com/oasis'))
        self.assertTrue(ftp.is_dir('ftp://ftp.pjm.com/oasis/'))
        self.assertTrue(ftp.is_dir('/oasis/'))
        self.assertTrue(ftp.is_dir('/oasis'))
        self.assertFalse(ftp.is_dir('/oasis/CBMID.pdf'))
        self.assertFalse(ftp.is_dir('oasis/CBMID.pdf'))
        self.assertFalse(ftp.is_dir('fakefile.ext'))
        ftp.quit ()

    def test_listdir(self):
        ftp = ez_ftp.FTP('ftp.pjm.com')
        self.assertEqual(35, len(ftp.listdir('ftp://ftp.pjm.com/oasis/')))
        tpl = ez_ftp.listdir('ftp://ftp.pjm.com/oasis/CBMID.pdf')[0]
        self.assertTrue(tpl.name, 'CBMID.pdf')
        self.assertTrue(tpl.modified > dtdt(2021, 1, 20, 10, 56))
        self.assertEqual(tpl.size, 160160)
        self.assertEqual(tpl.is_dir, False)

    def test_walk(self):
        # TODO: write FTP.walk() test script
        pass

class TestFunctions(unittest.TestCase):
    def setUp(self):
        print('')
        print(r"Calling TestFunctions.setUp()...")

    def test_tearDown(self):
        print('')
        print(r"Calling .tearDown()...")

    def test_url_join(self):
        # url_join(scheme, netloc, path)
        s = ez_ftp.url_join('', '', '')
        self.assertEqual(s, '')
        s = ez_ftp.url_join('', 'ftp.pjm.com', '')
        self.assertEqual(s, 'ftp://ftp.pjm.com')
        s = ez_ftp.url_join('ftp', 'ftp.pjm.com', '')
        self.assertEqual(s, 'ftp://ftp.pjm.com')
        s = ez_ftp.url_join('', 'ftp.pjm.com', 'oasis')
        self.assertEqual(s, 'ftp://ftp.pjm.com/oasis')
        s = ez_ftp.url_join('FTP', 'ftp.pjm.com', 'oasis')
        self.assertEqual(s, 'FTP://ftp.pjm.com/oasis')
        s = ez_ftp.url_join('FTP', 'ftp.pjm.com', 'oasis/CBMID.pdf')
        self.assertEqual(s, 'ftp://ftp.pjm.com/oasis/CBMID.pdf')

    def test_url_split(self):
        # def url_split(host_or_url, source_address: tuple = None)
        # return FTPPathParts(scheme, host, path, _dirname, _basename, url)
        tpl = ez_ftp.url_split(host_or_url = 'ftp.pjm.com')
        self.assertEqual(tpl.basename, '')
        self.assertEqual(tpl.dirname, '')
        self.assertEqual(tpl.path, '')
        self.assertEqual(tpl.netloc, 'ftp.pjm.com')
        self.assertEqual(tpl.scheme, 'ftp')
        self.assertEqual(tpl.url, 'ftp://ftp.pjm.com')

        tpl = ez_ftp.url_split(host_or_url = 'ftp://ftp.pjm.com/oasis/CBMID.pdf')
        self.assertEqual(tpl.basename, 'CBMID.pdf')
        self.assertEqual(tpl.dirname, '/oasis')
        self.assertEqual(tpl.path, '/oasis/CBMID.pdf')
        self.assertEqual(tpl.netloc, 'ftp.pjm.com')
        self.assertEqual(tpl.scheme, 'ftp')
        self.assertEqual(tpl.url, 'ftp://ftp.pjm.com/oasis/CBMID.pdf')

    def test_new_session(self):
        ez_ftp.new_session(ftp_url = 'ftp.pjm.com')
        ez_ftp._global_ftp.quit()
        ez_ftp.new_session(ftp_url = 'ftp://ftp.pjm.com')
        ez_ftp.new_session(ftp_url = 'ftps://ftp.pjm.com')
        ez_ftp.new_session(ftp_url = 'FTP://ftp.pjm.com')
        ez_ftp.new_session(ftp_url = 'FTPS://ftp.pjm.com')
        ez_ftp._global_ftp.quit()

    def test_stats(self):
        stats = ez_ftp.stats('ftp://ftp.pjm.com/oasis/CBMID.pdf')
        self.assertEqual(stats.scheme, 'ftp', f'scheme should be "ftp", but is "{stats.scheme}"')
        self.assertEqual(stats.netloc, 'ftp.pjm.com',
                         f'netloc should be "ftp.pjm.com", but is "{stats.netloc}"')
        self.assertEqual(stats.path, '/oasis/CBMID.pdf',
                         f'path should be "/oasis/CBMID.pdf", but is "{stats.path}"')
        self.assertEqual(stats.dirname, '/oasis',
                         f'dirname should be "/oasis", but is "{stats.dirname}"')
        self.assertEqual(stats.basename, 'CBMID.pdf',
                         f'basename should be "CBMID.pdf, but is "{stats.basename}"')
        self.assertTrue(stats.modified > dtdt(year=2021, month = 1, day = 20,
                                              hour = 14, minute = 56, second = 15),
                         f'modified should be 2021-01-20 14:56:15, but is {stats.modified}')
        self.assertEqual(stats.size, 160160,
                         f'size should be 177706, but is "{stats.size}"')
        stats = ez_ftp.stats('oasis/CBMID.pdf')
        stats = ez_ftp.stats('oasis/')
        self.assertEqual(stats.scheme, 'ftp', f'scheme should be "ftp", but is "{stats.scheme}"')
        self.assertEqual(stats.netloc, 'ftp.pjm.com',
                         f'netloc should be "ftp.pjm.com", but is "{stats.netloc}"')
        self.assertEqual(stats.path, 'oasis/',
                         f'path should be "oasis/", but is "{stats.path}"')
        self.assertEqual(stats.dirname, 'oasis/',
                         f'dirname should be "oasis/", but is "{stats.dirname}"')
        self.assertEqual(stats.basename, '',
                         f'basename should be "", but is "{stats.basename}"')
        self.assertEqual(stats.modified, None,
                         f'modified should be None, but is {stats.modified}')
        self.assertEqual(stats.size, None,
                         f'size should be None, but is "{stats.size}"')
        stats = ez_ftp.stats('oasis')

    def test_url_join(self):
        self.assertEqual(ez_ftp.url_join('ftp','ftp.pjm.com','oasis'), 'ftp://ftp.pjm.com/oasis')
        self.assertEqual(ez_ftp.url_join('ftp','ftp.pjm.com', ''), 'ftp://ftp.pjm.com')
        self.assertEqual(ez_ftp.url_join('ftp','ftp.pjm.com'), 'ftp://ftp.pjm.com')
        self.assertEqual(ez_ftp.url_join('','ftp.pjm.com'), 'ftp://ftp.pjm.com')
        self.assertEqual(ez_ftp.url_join('','ftp.pjm.com','/oasis/'), 'ftp://ftp.pjm.com/oasis/')
        self.assertEqual(ez_ftp.url_join('FTPS','ftp.pjm.com','/oasis/'), 'FTPS://ftp.pjm.com/oasis/')

    def test_basename(self):
        self.assertEqual(ez_ftp.basename('ftp://ftp.pjm.com/oasis/CBMID.pdf'), 'CBMID.pdf')
        self.assertEqual(ez_ftp.basename('ftp://ftp.pjm.com/oasis/'), '')
        self.assertEqual(ez_ftp.basename('ftp://ftp.pjm.com/oasis'), '')

    def test_dirname(self):
        self.assertEqual(ez_ftp.dirname('ftp://ftp.pjm.com/oasis/CBMID.pdf'), '/oasis')
        self.assertEqual(ez_ftp.dirname('ftp://ftp.pjm.com/oasis/'), '/oasis')
        self.assertEqual(ez_ftp.dirname('ftp://ftp.pjm.com/oasis'), '/oasis')

    def test_modified(self):
        pass

    def test_size(self):
        self.assertEqual(ez_ftp.size('ftp://ftp.pjm.com/oasis/CBMID.pdf'), 160160)
        self.assertEqual(ez_ftp.size('ftp://ftp.pjm.com/oasis'), None)
        self.assertEqual(ez_ftp.size('ftp://ftp.pjm.com/oasis/'), None)
        self.assertEqual(ez_ftp.size('ftp://ftp.pjm.com'), None)

    def test_download_and_compare_to_local(self):
        ez_ftp.download('ftp://ftp.pjm.com/oasis/CBMID.pdf', tgt_folder = 'c:/temp')
        ez_ftp.download('ftp.pjm.com/oasis/CBMID.pdf', tgt_folder = 'c:/temp')
        x = ez_ftp.compare_to_local('c:/temp/CBMID.pdf', 'ftp.pjm.com/oasis/CBMID.pdf',
                                 hash_check=False)
        self.assertTrue(x, "downloaded 'ftp.pjm.com/oasis/CBMID.pdf' but comparison to local file failed; (no hash_check requested).")
        x = ez_ftp.compare_to_local('c:/temp/CBMID.pdf', 'ftp.pjm.com/oasis/CBMID.pdf',
                                 hash_check=True)
        self.assertTrue(x, "downloaded 'ftp.pjm.com/oasis/CBMID.pdf' but comparison to local file failed; (hash_check requested).")

    def test_listdir(self):
        self.assertEqual(len(ez_ftp.listdir('ftp://ftp.pjm.com/oasis/')), 35)
        tpl = ez_ftp.listdir('ftp://ftp.pjm.com/oasis/CBMID.pdf')[0]
        self.assertEqual(tpl.name, 'CBMID.pdf')
        self.assertTrue(tpl.modified > dtdt(2021, 1, 20, 10, 56))
        self.assertEqual(tpl.size, 160160)
        self.assertEqual(tpl.is_dir, False)

    def test_is_dir(self):
        self.assertFalse(ez_ftp.is_dir('ftp://ftp.pjm.com/oasis/CBMID.pdf'))
        self.assertTrue(ez_ftp.is_dir('ftp://ftp.pjm.com/oasis/'))
        self.assertTrue(ez_ftp.is_dir('ftp://ftp.pjm.com/oasis'))
        self.assertTrue(ez_ftp.is_dir('ftp://ftp.pjm.com/'))
        self.assertTrue(ez_ftp.is_dir('ftp://ftp.pjm.com'))

    def test_exists(self):
        self.assertTrue(ez_ftp.exists('ftp://ftp.pjm.com/oasis/CBMID.pdf'))
        self.assertTrue(ez_ftp.exists('ftp://ftp.pjm.com/oasis'))
        self.assertTrue(ez_ftp.exists('ftp://ftp.pjm.com/oasis/'))
        # self.assertRaises(AssertionError, ez_ftp.exists('/oasis/'))



if __name__ == '__main__':
    ### 2 - invoke the framework ###
    # invoke the unittest framework
    # unittest.main() will capture all fo the tests
    # and run them 1-by-1.
    unittest.main()

