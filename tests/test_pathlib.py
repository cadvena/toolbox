import os, stat, shutil
import unittest
from toolbox.pathlib import Path
from toolbox import path
import pathlib


class TestPath(unittest.TestCase):
    def setUp(self):
        print("\nCalling TestOSWrapper.setUp()...")
        self.path_str = 'c:/gmom/mom/stem.suffix'
        self.root_str = 'c:/gmom'
        p = pathlib.Path(self.root_str)
        p = pathlib.Path(self.path_str)
        if p.parent.exists():
            raise FileExistsError
        p.parent.mkdir (parents = True, exist_ok = True)

    def tearDown(self):
        print("\nCalling TestOSWrapper.tearDown()...")
        # p = path_str.split('/')[:2]
        # p = pathlib.py.Path(p[0] + '/' + p[1])
        p = pathlib.Path(self.root_str)
        if p.exists():
            shutil.rmtree(p)

    def test_Path_init(self):
        path_str = self.path_str
        p = Path(path_str)
        self.assertEqual(p.prev_wds[0], os.getcwd())
        self.assertEqual(p.ignore_errors, False)
        # self.assertEqual(p.find_implied, True)
        # self.assertEqual(p.make_assumptions, True)
        # self.assertEqual(p.basename, 'stem.suffix')
        # self.assertEqual(p.ext, '.suffix')
        self.assertEqual (pathlib.Path(path_str).parent, p.parent)

        a = pathlib.Path(path_str).parents
        b = p.parents
        self.assertEqual (len(a), len(b))
        for i in range(len(a)):
            self.assertEqual(str(a[i]), str(b[i]))

        self.assertEqual (str(pathlib.Path(path_str).joinpath('abc/me.you')),
                          str(p.joinpath('abc/me.you')))
        self.assertEqual (False, p.exists())
        self.assertEqual (pathlib.Path(path_str).exists(), p.exists())
        self.assertEqual (pathlib.Path(path_str).with_suffix('.blue'),
                          p.with_suffix('.blue'))
        self.assertEqual (pathlib.Path(path_str).suffix, p.suffix)
        self.assertEqual (pathlib.Path(path_str).suffixes, p.suffixes)
        self.assertEqual (False, p.is_dir(make_assumptions=False))
        self.assertEqual (False, p.is_dir(make_assumptions=True))
        self.assertEqual (pathlib.Path(path_str).is_dir(),
                          p.is_dir(make_assumptions=False))
        self.assertEqual (pathlib.Path(path_str).name, p.name)
        self.assertEqual (pathlib.Path(path_str).root, p.root)
        self.assertEqual (pathlib.Path(path_str).anchor, p.anchor)
        self.assertEqual (pathlib.Path(path_str).drive, p.drive().str)
        self.assertEqual (pathlib.Path(path_str).absolute(), p.absolute())
        self.assertEqual (True, p.is_file(make_assumptions=True))
        self.assertEqual (False, p.is_file(make_assumptions=False))
        self.assertEqual (pathlib.Path(path_str).is_file(),
                          p.is_file(make_assumptions=False))
        self.assertEqual (pathlib.Path(path_str).stem, p.stem)
        self.assertEqual (pathlib.Path(path_str).parts, p.parts)
        if pathlib.Path(path_str).exists():
            self.assertEqual (pathlib.Path(path_str).stat(), p.stat())
        self.assertEqual (pathlib.Path(path_str).expanduser(), p.expanduser())
        if os.name != 'nt':
            self.assertEqual (pathlib.Path(path_str).group(), p.group())
        self.assertEqual (pathlib.Path(path_str).is_absolute(), p.is_absolute())
        self.assertEqual (pathlib.Path(path_str).home(), p.home())
        self.assertEqual (pathlib.Path(path_str).exists(), p.exists())

    def test_Path_is_dir_is_file_drive(self):
        # create good temp_dir
        # temp_dir = os.path.join(os.environ['temp'], 'temp_dir')  # caused PermissionError: [WinError 5] Access is denied
        temp_dir = os.path.join("C:/temp", 'temp_dir')
        if os.path.exists(temp_dir):
            os.chmod (path = temp_dir, mode = stat.S_IWRITE)
            shutil.rmtree(temp_dir)
        os.mkdir(temp_dir)
        os.chmod(path = temp_dir, mode = stat.S_IWRITE)

        fp = Path(temp_dir)
        self.assertTrue(fp.exists())
        self.assertTrue(fp.is_dir())
        self.assertTrue(fp.is_dir(make_assumptions = True))
        self.assertTrue(fp.is_dir(make_assumptions = False))
        self.assertFalse(fp.is_file())
        self.assertFalse(fp.is_file(make_assumptions = True))
        self.assertFalse(fp.is_file(make_assumptions = False))

        temp_dir = os.path.abspath(temp_dir)
        drv = str(pathlib.Path(temp_dir).drive)
        fr_drv = fp.drive().str
        self.assertEqual(type(drv), str)
        self.assertEqual(type(fr_drv), str)
        self.assertTrue(isinstance(fp, Path))
        self.assertEqual(fp.drive().str, drv)
        self.assertEqual(fp.drive(find_implied = True).str, drv)
        self.assertEqual(fp.drive(find_implied = False).str, drv)

        os.chmod(path = temp_dir, mode = stat.S_IWRITE)
        shutil.rmtree(temp_dir)

        # no_dir: valid dir name but dir does not exist
        no_dir = os.path.join ("C:/temp", 'no_dir')
        if os.path.exists (no_dir):
            os.remove (no_dir)
            shutil.rmtree (no_dir)

        fp = Path(no_dir)
        self.assertFalse(fp.exists ())
        self.assertTrue(fp.is_dir())
        self.assertTrue(fp.is_dir (make_assumptions = True))
        self.assertFalse(fp.is_dir (make_assumptions = False))
        self.assertFalse(fp.is_file ())
        self.assertFalse(fp.is_file (make_assumptions = True))
        self.assertFalse(fp.is_file (make_assumptions = False))

        temp_dir = os.path.abspath (no_dir)
        drv = pathlib.Path(no_dir).drive
        self.assertEqual (fp.drive().str, drv)
        self.assertEqual (fp.drive(find_implied = True).str, drv)
        self.assertEqual (fp.drive(find_implied = False).str, drv)


        # create temp_file
        temp_file = os.path.join("C:/temp", 'temp.txt')
        if os.path.exists(temp_file):
            os.chmod (path = temp_file, mode = stat.S_IWRITE)
            os.remove(temp_file)
        with open(temp_file, 'w') as file:
            file.write('abc\ndef')

        fp = Path (temp_file)
        self.assertTrue(fp.exists ())
        self.assertFalse(fp.is_dir ())
        self.assertFalse(fp.is_dir (make_assumptions = True))
        self.assertFalse(fp.is_dir (make_assumptions = False))
        self.assertTrue(fp.is_file ())
        self.assertTrue(fp.is_file (make_assumptions = True))
        self.assertTrue(fp.is_file (make_assumptions = False))

        temp_dir = os.path.abspath (temp_file)
        drv = pathlib.Path(temp_file).drive
        self.assertEqual(fp.drive().str, drv)
        self.assertEqual(fp.drive(find_implied = True).str, drv)
        self.assertEqual(fp.drive(find_implied = False).str, drv)
        os.chmod(path = temp_file, mode = stat.S_IWRITE)
        os.remove (temp_file)


        # no_file: valid file name but file does not exist
        no_file = os.path.join("C:/temp", 'no_file.txt')
        if os.path.exists(no_file):
            shutil.rmtree(no_file)

        fp = Path (no_file)
        self.assertFalse(fp.exists ())
        self.assertFalse(fp.is_dir ())
        self.assertFalse(fp.is_dir (make_assumptions = True))
        self.assertFalse(fp.is_dir (make_assumptions = False))
        self.assertTrue(fp.is_file())
        self.assertTrue(fp.is_file(make_assumptions = True))
        self.assertFalse(fp.is_file(make_assumptions = False))

        temp_dir = os.path.abspath (no_file)
        drv = pathlib.Path(no_file).drive
        self.assertEqual(fp.drive().str, drv)
        self.assertEqual(fp.drive(find_implied = True).str, drv)
        self.assertEqual(fp.drive(find_implied = False).str, drv)

    def test_drive_parent(self):
        # self.assertEqual (Path ('C:/temp').find_implied, True)
        self.assertEqual(Path('C:/temp').drive_parent().str, 'C:\\')
        self.assertEqual(Path('C:/temp').drive_parent(find_implied = True),
                         pathlib.Path('C:/'))
        self.assertEqual(Path('C:/temp').drive_parent(find_implied =  False),
                         pathlib.Path('C:/'))

        self.assertEqual (Path ('C:/temp').drive_parent().str, 'C:\\')
        self.assertEqual(Path('/temp').drive_parent(find_implied = True),
                         pathlib.Path ('C:/'))
        self.assertEqual(Path('/temp').drive_parent(find_implied =  False).str,
                         "\\")

    def test_Path_folder_part(self):
        # self.path_str = 'c:/gmom/mom/stem.suffix'
        self.root_str = 'c:/gmom'
        p = Path(self.path_str)
        r = Path(self.root_str)
        self.assertEqual(p.str, str(pathlib.Path(self.path_str)))
        self.assertEqual(p.parent.str, str(pathlib.Path(self.path_str).parent))
        self.assertEqual(p.folder_part().str, str(pathlib.Path(self.path_str).parent))
        self.assertEqual(p.folder_part().str, p.parent.str)
        self.assertEqual(r.folder_part().str.replace("/","\\"), self.root_str.replace("/","\\"))


if __name__ == '__main__':
    ### 2 - invoke the framework ###
    # invoke the unittest framework
    # unittest.main() will capture all fo the tests
    # and run them 1-by-1.
    unittest.main ()