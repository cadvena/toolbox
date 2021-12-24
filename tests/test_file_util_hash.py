# 1 - Import unittest (find 2 under "if __name__ == '__main__'")
import unittest
from toolbox.file_util import hash as h
from time import sleep
import os


class TestHash(unittest.TestCase):
    def setUp(self):
        print('')
        print(r"Calling .setUp()...")
        # if os.path.exists(self.key_filename):
        #     os.remove(self.key_filename)

    def tearDown(self):
        print('')
        print(r"Calling .tearDown()...")

    def test_sha256_hash_and_has_match(self):
        # test sha256_hash()
        files = 'delete.me0', 'delete.me1', 'delete.me2'
        bin = b'hello world', b'hello world', b'bye-bye world'
        txt = 'hello world', 'hello world', 'bye-bye world'
        inputs = [[bin, 'wb'], [txt, 'w']]
        for inpt in inputs:
            strings, mode = inpt
            for j in range(len(files)):
                with open(files[j], mode) as writer:
                    writer.write(strings[j])
                h1 = h.sha256_hash(files[j])
                self.assertTrue(isinstance(h1, str))
                h2 = h.sha256_hash(files[j])
                self.assertEqual(h1, h2)
                del h1
                del h2
                h1 = h.md5_hash(files[j])
                self.assertTrue(isinstance(h1, str))
                h2 = h.md5_hash(files[j])
                self.assertEqual(h1, h2)
            # SHA_256 Hash
            # delete.me0 is identical to delete.me1, so hashes should match
            self.assertEqual(h.sha256_hash(files[0]), h.sha256_hash(files[1]))
            self.assertTrue(h.hash_match(files[0], files[1]))
            # delete.me0 has different content from delete.me2, so hashes should NOT match
            self.assertNotEqual(h.sha256_hash(files[0]), h.sha256_hash(files[2]))
            self.assertFalse(h.hash_match(files[0], files[2]))
            # delete.me1 has different content from delete.me2, so hashes should NOT match
            self.assertNotEqual(h.sha256_hash(files[1]), h.sha256_hash(files[2]))
            self.assertFalse(h.hash_match(files[1], files[2]))

            # MD5 Hash
            # delete.me0 is identical to delete.me1, so hashes should match
            self.assertEqual(h.md5_hash(files[0]), h.md5_hash(files[1]))
            self.assertTrue(h.hash_match(files[0], files[1], hash_method = 1))
            # delete.me0 has different content from delete.me2, so hashes should NOT match
            self.assertNotEqual(h.md5_hash(files[0]), h.md5_hash(files[2]))
            self.assertFalse(h.hash_match(files[0], files[2], hash_method = 1))
            # delete.me1 has different content from delete.me2, so hashes should NOT match
            self.assertNotEqual(h.md5_hash(files[1]), h.md5_hash(files[2]))
            self.assertFalse(h.hash_match(files[1], files[2], hash_method = 1))


if __name__ == '__main__':
    ### 2 - invoke the framework ###
    # invoke the unittest framework
    # unittest.main() will capture all fo the tests
    # and run them 1-by-1.
    unittest.main()
