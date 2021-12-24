import re
import unittest
from toolbox.find_proxy_for_url import is_plain_host_name, dns_domain_is, \
                                       host_parse, local_host_or_domain_is, \
                                       is_resolvable


class TestClass(unittest.TestCase):
    def setUp(self):
        print("\nCalling TestOSWrapper.setUp()...")
        self.bad_hosts = ['www', 'notawebsite.bad']
        self.good_hosts = ['pjm.com', 'www.pjm.com', 'google.com']


    def tearDown(self):
        print("\nCalling TestOSWrapper.tearDown()...")

    def test_host_parse(self):
        # urls = ['https://www.youtube.com/watch?v=YR12Z8f1Dh8&feature=relmfu',
        #             'youtube.com/watch?v=YR12Z8f1Dh8&feature=relmfu',
        #             'pjm.com/folder1/folder2/index.html',
        #             'pjm.com/oasis/index.html',
        #             'www.pjm.com',
        #             'pjm.com',
        #             'www.',
        #             'www',
        #             ]
        h = host_parse('www')
        self.assertEqual('', h.domain)
        self.assertEqual('', h.domain_extension)
        self.assertEqual('', h.resource_owner)
        self.assertEqual('www', h.subdomain)

        h = host_parse('pjm.com')
        self.assertEqual('pjm.com', h.domain)
        self.assertEqual('com', h.domain_extension)
        self.assertEqual('pjm', h.resource_owner)
        self.assertEqual('', h.subdomain)

        h = host_parse('www.pjm.com')
        self.assertEqual('pjm.com', h.domain)
        self.assertEqual('com', h.domain_extension)
        self.assertEqual('pjm', h.resource_owner)
        self.assertEqual('www', h.subdomain)

        h = host_parse('http://www.pjm.com')
        self.assertEqual('pjm.com', h.domain)
        self.assertEqual('com', h.domain_extension)
        self.assertEqual('pjm', h.resource_owner)
        self.assertEqual('www', h.subdomain)

        h = host_parse('http://www.pjm.com/oasis/index.html')
        self.assertEqual('pjm.com', h.domain)
        self.assertEqual('com', h.domain_extension)
        self.assertEqual('pjm', h.resource_owner)
        self.assertEqual('www', h.subdomain)

    def test_is_plain_host_name(self):
        for host in self.good_hosts:
            x = is_plain_host_name(host)
            self.assertFalse(x)
        for host in self.bad_hosts:
            if "." not in host:
                x = is_plain_host_name(host)
                self.assertTrue(x)

    def test_dns_domain_is(self):
        matches = [['pjm.com', 'www.pjm.com'],
                   ['www.pjm.com', 'pjm.com'],
                   ['www.pjm.com', 'media.pjm.com']
                   ]
        mismatches = [['www', 'netscope.com'],
                      ['pjm.com', 'google.com']
                      ]
        for m in matches:
            x = dns_domain_is(m[0], m[1])
            self.assertTrue(x)
        for m in mismatches:
            x = dns_domain_is(m[0], m[1])
            self.assertFalse(x)

    def test_local_host_or_domain_is(self):
        matches = [['pjm.com', 'www.pjm.com'],
                   ['www.pjm.com', 'pjm.com'],
                   ['www.pjm.com', 'media.pjm.com'],
                   ['www', 'netscope.com'],
                   ]
        mismatches = [
                      ['pjm.com', 'google.com'],
                      ['netscope.com', 'www'],
            ]
        for url1, url2 in matches:
            b = local_host_or_domain_is(url1, url2)
            self.assertTrue(b)
        for url1, url2 in mismatches:
            b = local_host_or_domain_is(url1, url2)
            self.assertFalse(b)

    def test_is_resolvable(self):
        self.assertTrue(is_resolvable('www.pjm.com'))
        self.assertTrue(is_resolvable('pjm.com'))
        self.assertTrue(is_resolvable('www.google.com'))
        self.assertTrue(is_resolvable('google.com'))
        self.assertFalse(is_resolvable('some.fake.faker'))


if __name__ == '__main__':
    ### 2 - invoke the framework ###
    # invoke the unittest framework
    # unittest.main() will capture all fo the tests
    # and run them 1-by-1.
    unittest.main ()
