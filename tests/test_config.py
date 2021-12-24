import unittest
from toolbox import config
from toolbox.pathlib import Path
from toolbox.config import Config, dict_recursive_update, dict_recursive_update_if_none
import tempfile
from toolbox.pathlib import rmtree
from toolbox.temp_file import TempFile, TempDir
from toolbox.appdirs import site_temp_dir
import os

temp_dir = site_temp_dir(Path(__file__).stem)

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.init_dir = os.getcwd()
        self.init_dir = Path(__file__).parent.str

    def tearDown(self):
        os.chdir(self.init_dir)

    def test_init(self):
        # fp = tempfile.TemporaryDirectory()
        with tempfile.TemporaryDirectory() as fp:
            # os.chdir(fp.name)
            os.chdir(fp)
            # cfg_file = os.path.join (fp.name, 'test.config')
            cfg_file = os.path.join (fp, 'test.config')
            # instantiate Config
            cfg = Config (file = cfg_file, auto_save = False)
            self.assertTrue(isinstance(cfg, Config))
            self.assertEqual(cfg.filename, cfg_file, 'Filename check')
            self.assertEqual(cfg.auto_save, False)
            self.assertEqual(cfg.dict, {}, 'Since this is a new config file, .dict should start '
                                           'out as an empty dict')
            del cfg
            cfg = Config (file = cfg_file)
            self.assertEqual(cfg.auto_save, True)
            os.chdir (self.init_dir)
        # fp.cleanup()

    def test_auto_save(self):
        with tempfile.TemporaryDirectory() as fp:
            os.chdir(fp)

            # Test saving new config file
            cfg_file = os.path.join (fp, 'test.config')
            # test auto_save == False
            cfg = Config(file = cfg_file, auto_save = False)
            cfg.set('color', 'blue')
            self.assertEqual(cfg['color'], 'blue')
            cfg['fruit'] = 'apple'
            self.assertEqual(cfg['fruit'], 'apple')
            cfg.save()
            del cfg

            # Test reading config, changing and not saving
            cfg = Config (file = cfg_file, auto_save = False)
            self.assertEqual(cfg['color'], 'blue')
            self.assertEqual(cfg['fruit'], 'apple')
            cfg.set('color', 'red')
            cfg['fruit'] = 'pear'
            del cfg
            cfg = Config (file = cfg_file, auto_save = False)
            b = cfg.exists ('color')
            self.assertTrue(b)
            b = cfg.exists ('fruit')
            self.assertEqual(b, True)

            # Test reading config, changing and saving
            cfg = Config (file = cfg_file, auto_save = True)
            cfg.set('color', 'red')
            cfg['fruit'] = 'pear'
            del cfg
            cfg = Config (file = cfg_file, auto_save = True)
            self.assertEqual(cfg['color'], 'red')
            self.assertEqual(cfg['fruit'], 'pear')

            os.chdir(self.init_dir)

    def test_clear(self):
        with tempfile.TemporaryDirectory () as fp:
            os.chdir (fp)

            # Test saving new config file
            cfg_file = os.path.join (fp, 'test.config')
            # test auto_save == False
            cfg = Config (file = cfg_file, auto_save = False)
            cfg.set ('color', 'blue')
            self.assertEqual(cfg['color'], 'blue')
            cfg['fruit'] = 'apple'
            self.assertEqual(cfg['fruit'], 'apple')
            cfg.clear()
            self.assertEqual(len(cfg.keys()), 0)

            os.chdir (self.init_dir)

    def test_filename(self):
        # fp = tempfile.TemporaryDirectory()
        # fp = Path(TempDir().path)
        with tempfile.TemporaryDirectory() as fp:
            os.chdir(fp)
            # Test saving new config file
            cfg_file1 = os.path.join (fp, 'test1.config')
            cfg_file2 = os.path.join (fp, 'test2.config')
            # test auto_save == False
            cfg = Config (file = cfg_file1, auto_save = True)
            cfg.set ('color', 'purple')
            cfg['fruit'] = 'apple'
            cfg.file = cfg_file2
            del cfg
            with open(cfg_file1, 'r') as f1:
                lines1 = f1.readlines()
            cfg1 = Config(file = cfg_file1, auto_save = False)
            with open(cfg_file2, 'r') as f2:
                lines2 = f2.readlines ()
            cfg2 = Config (file = cfg_file2, auto_save = False)
            self.assertEqual (cfg2['color'], 'purple')
            self.assertEqual (cfg2['fruit'], 'apple')
            self.assertEqual(cfg1, cfg2)
            os.chdir(self.init_dir)
        # fp.cleanup()
        # fp.rmtree()


        self.assertEqual(lines1, lines2)

    def test_is_path_like(self):
        plike = Config.is_path_like
        self.assertTrue(plike(r'C:\path\path2\file.ext'))
        self.assertTrue(plike(r'C:/path/path.2/file.ext'))
        # self.assertTrue(plike(r'C:/path/path2/file.ext/'))
        self.assertTrue(plike(r'C:/path/path2'))
        # self.assertFalse(plike(r'C:////path/path2/file.ext'))
        self.assertTrue(plike(r'::/path/path2/file.ext'))
        self.assertTrue(plike(r'../path/path2'))

    def test_dict(self):
        d = {'color': 'blue', 'fruit': 'apple'}
        cfg = Config (file = 'delete_me.config', dict_in = d, auto_save = False)
        # # copy all values of dict d into cfg
        # for k, v in d.items():
        #     cfg[k] = v
        self.assertEqual(d, cfg.dict)
        self.assertTrue(isinstance(cfg, Config))
        self.assertEqual(type(cfg.dict), dict)

        d2 = {'spin': 'up', 'number': 3.14}
        for k in d2.keys():
            self.assertFalse(cfg.exists(k))
        cfg.dict = d2
        for k in d2.keys():
            self.assertTrue(cfg.exists(k))
        self.assertEqual(len(cfg.keys()), 4)
        self.assertEqual(cfg['color'], 'blue')
        self.assertEqual(cfg['fruit'], 'apple')
        self.assertEqual(cfg['spin'], 'up')

    def test_pop(self):
        d = {'color': 'blue', 'fruit': 'apple'}
        cfg = Config (file = 'delete_me.config', dict_in = d, auto_save = False)
        self.assertEqual(d, cfg.dict)
        self.assertTrue('color' in cfg.keys())
        self.assertEqual(cfg.pop('color'), 'blue')
        self.assertTrue('color' not in cfg.keys())
        with self.assertRaises (KeyError):
            cfg.pop ('color')
        self.assertEqual(cfg.pop('color', 'orange'), 'orange')

    def test_popitem(self):
        d = {'color': 'blue', 'fruit': 'apple', 'name':'Bob'}
        cfg = Config (file = 'delete_me.config', dict_in = d, auto_save = False)
        cfg.popitem()
        self.assertFalse(cfg.exists('name'))
        self.assertTrue(cfg.exists('fruit'))

    def test_parameters(self):
        d = {'color': 'blue', 'fruit': 'apple'}
        cfg = Config (file = 'delete_me.config', dict_in = d, auto_save = False)
        self.assertEqual(cfg.parameters, d.keys())

    def test_set(self):
        d = {'color': 'blue', 'fruit': 'apple'}
        cfg = Config (file = 'delete_me.config', dict_in = d, auto_save = False)
        self.assertEqual(cfg['color'], 'blue')
        cfg.set('color', 'orange')
        self.assertEqual(cfg['color'], 'orange')
        cfg.set('shape', 'circle')
        self.assertEqual(cfg['shape'], 'circle')

    def test_update(self):
        d = {'color': 'blue', 'fruit': 'apple'}
        cfg = Config (file = 'delete_me.config', dict_in = d, auto_save = False)
        # # copy all values of dict d into cfg
        # for k, v in d.items():
        #     cfg[k] = v
        self.assertEqual(d, cfg.dict)
        self.assertTrue(isinstance(cfg, Config))
        self.assertEqual(type(cfg.dict), dict)

        d2 = {'spin': 'up', 'number': 3.14}
        for k in d2.keys():
            self.assertFalse(cfg.exists(k))
        cfg.update(d2)
        for k in d2.keys():
            self.assertTrue(cfg.exists(k))
        self.assertEqual(len(cfg.keys()), 4)
        self.assertEqual(cfg['color'], 'blue')
        self.assertEqual(cfg['fruit'], 'apple')
        self.assertEqual(cfg['spin'], 'up')

    def test_update_if_none(self):
        d = {'color': 'blue', 'fruit': 'apple'}
        cfg = Config (file = 'delete_me.config', dict_in = d, auto_save = False)
        cfg.update_if_none({'color': 'orange'})
        self.assertEqual(cfg['color'], 'blue')
        cfg.update_if_none({'shape': 'triangle'})
        self.assertEqual(cfg['shape'], 'triangle')

    def test_setdefault(self):
        d = {'color': 'blue', 'fruit': 'apple'}
        cfg = Config (file = 'delete_me.config', dict_in = d, auto_save = False)
        self.assertEqual(cfg.setdefault('color', 'green'), 'blue')
        self.assertEqual(cfg['color'], 'blue')
        self.assertEqual(cfg.setdefault('shape', 'cube'), 'cube')
        self.assertEqual(cfg['shape'], 'cube')

    # def setdefault(self, parameter_name: str, parameter_value):
    #     """Ensure we launch auto-save after 'setdefault' of dict.item()"""
    #     result = super().setdefault(parameter_name, parameter_value)
    #     if self.auto_save:
    #         self.save()
    #     return result

    def test_copy(self):
        d = {'color': 'blue', 'fruit': 'apple'}
        cfg = Config (file = 'delete_me.config', dict_in = d, auto_save = False)
        cfg2 = cfg.copy(file = 'delete_me.too')
        self.assertEqual(cfg, cfg2)
        cfg2['shape'] = 'rombus'
        self.assertNotEqual(cfg, cfg2)
        self.assertEqual(len(cfg), 2)
        self.assertEqual(len(cfg2), 3)


class TestDict_recursive_update(unittest.TestCase):
    def setUp(self):
        self.init_dir = os.getcwd()
        self.init_dir = Path(__file__).parent.str

        # dict_recursive_update_if_none
        self.cfg_path = Path(temp_dir).joinpath('test.cfg')
        if self.cfg_path.exists():
            self.cfg_path.delete()

        self.exist = {'param1': 'val1',
                      'cat2': {'cat2.1': 'val2.1',
                               'cat2.2': 'val2.2'
                               }
                      }

    def test_recursive_update_if_none(self):
        # existing dict
        exist = self.exist
        # updates to apply
        updates = {}
        cfg = Config(file = self.cfg_path, dict_in = exist, auto_save = False)
        dict2 = exist.copy()
        # baseline:
        self.assertEqual(exist, cfg.dict)
        self.assertEqual(exist, dict2)
        # for key in exist.keys():
        #     self.assertEqual(exist[key], cfg[key], f"Assert exist[key] == cfg[key]; key is {key}")

        # send an empty dict of updates.  Should have no affect
        cfg.update_if_none(dict_of_parameters = {}, recurse = True)
        dict2 =
        self.assertEqual(exist, cfg.dict)

        # update where not exists at top level
        cfg.update_if_none(dict_of_parameters = {'cat3': {'cat3.3': 'val3.3'}})
        expected = {'param1': 'val1',
                    'cat2': {'cat2.1': 'val2.1',
                             'cat2.2': 'val2.2'
                             },
                    'cat3': {'cat3.3': 'val3.3'},
                    }
        self.assertEqual(expected, cfg.dict)

        # try to overwrite existing key:value pair with new key:value pair
        # for update_if_none, this should have no effect
        cfg.recursive_updates = True
        cfg.update_if_none(dict_of_parameters = {'cat3': 'val error 3'})
        self.assertEqual(expected, cfg.dict)

        # try to add new cat2.3:val2.3.  This should work since
        # cat2.3 does not exist and cfg.recursive_updates == True.
        # Also try to change cat2.2, which should fail since a value exists already.
        cfg.recursive_updates = True
        updates = {'cat2': {'cat2.2': 'val2.2 error',
                            'cat2.3': 'val2.3',
                            },
                   }
        cfg.update_if_none(updates)
        expected = {'param1': 'val1',
                    'cat2': {'cat2.1': 'val2.1',
                             'cat2.2': 'val2.2',
                             'cat2.3': 'val2.3',
                             },
                    'cat3': {'cat3.3': 'val3.3'},
                    }
        self.assertEqual(expected, cfg.dict)

        # Try to a recursive update when recursive_updates is set to False.
        # No updates should be made
        cfg.recursive_updates = False
        updates = {'cat2': {'cat2.2': 'val2.2 error',
                            'cat2.4': 'val2.4 error',
                            },
                   }
        cfg.update_if_none(updates)
        self.assertEqual(expected, cfg.dict)

    def test_recursive_update(self):
        # existing dict
        exist = self.exist
        # updates to apply
        updates = {}
        cfg = Config(file = self.cfg_path, dict_in = exist, auto_save = False)
        # baseline:
        self.assertEqual(exist, cfg.dict)
        for key in exist.keys():
            self.assertEqual(exist[key], cfg[key], f"Assert exist[key] == cfg[key]; key is {key}")

        cfg.recursive_updates = True

        # send an empty dict of updates.  Should have no affect
        cfg.update(dict_of_parameters = {}, recurse = False)
        self.assertEqual(exist, cfg.dict)

        # update where not exists at top level
        cfg.update(dict_of_parameters = {'cat3': {'cat3.3': 'val3.3'}})
        expected = {'param1': 'val1',
                    'cat2': {'cat2.1': 'val2.1',
                             'cat2.2': 'val2.2'
                             },
                    'cat3': {'cat3.3': 'val3.3'},
                    }
        self.assertEqual(expected, cfg.dict)

        # try to overwrite existing key:value pair with new key:value pair
        # for update, this should work
        cfg.recursive_updates = True
        cfg.update(dict_of_parameters = {'cat3': {'cat3.3': 'val3.3 update'}})
        expected = {'param1': 'val1',
                    'cat2': {'cat2.1': 'val2.1',
                             'cat2.2': 'val2.2'
                             },
                    'cat3': {'cat3.3': 'val3.3 update'},
                    }
        self.assertEqual(expected, cfg.dict)

        # try to add new cat2.3:val2.3.  This should work since
        # cat2.3 does not exist and cfg.recursive_updates == True.
        # Also try to change cat2.2, which should work
        cfg.recursive_updates = True
        updates = {'cat2': {'cat2.2': 'val2.2 update',
                            'cat2.3': 'val2.3',
                            },
                   }
        cfg.update(updates)
        expected = {'param1': 'val1',
                    'cat2': {'cat2.1': 'val2.1',
                             'cat2.2': 'val2.2 update',
                             'cat2.3': 'val2.3',
                        },
                    'cat3': {'cat3.3': 'val3.3 update'},
                    }
        self.assertEqual(expected, cfg.dict)

        # Try to a recursive update when recursive_updates is set to False.
        # In this case sub-dicts will be overwritten entirely.
        cfg.recursive_updates = False
        updates = {'cat2': {'cat2.2': 'val2.2 wow',
                            'cat2.4': 'val2.4 wow',
                            },
                   }
        cfg.update(updates)
        expected = {'param1': 'val1',
                    'cat2': {'cat2.2': 'val2.2 wow',
                             'cat2.4': 'val2.4 wow',
                              },
                    'cat3': {'cat3.3': 'val3.3 update'},
                    }
        self.assertEqual(expected, cfg.dict)


class TestExamples (unittest.TestCase):
    # def setUp(self):
    #     pass
    #
    # def tearDown(self):
    #     pass
    #
    def test_examples(self):
        config.example_config_file_from_filename()
        config.example_config_file_from_appname()


if __name__ == '__main__':
    ### 2 - invoke the framework ###
    # invoke the unittest framework
    # unittest.main() will capture all fo the tests
    # and run them 1-by-1.
    unittest.main()