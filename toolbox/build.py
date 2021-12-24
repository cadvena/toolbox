import shutil
import os

from pjmlib.pathutils import Path
from pjmlib.dept.opd.buildutils import increment_version, push_to_nexus

app_name = 'pjmlib'

class PjmlibBuilder(AbstractBuilder):
    def __init__(self):
        super.__init__()


class AbstractBuilder(object):
    def __init__(self):
        self.topdir = Path(__file__).parent.absolute()
        self.version = '0.0.1'

    def run_full_build_cycle(self, run_test=True):
        self._increment_version()
        self._cleanup_last_build()
        self._create_build_copies()
        self._transpile_py2()
        if run_test:
            self._run_unit_tests_py2(True)
        self._build_wheels()
        self._upload_to_nexus()

    def run_py2_tests(self, run_slow_tests=False):
        self._cleanup_last_build()
        self._create_build_copies()
        self._transpile_py2()
        self._run_unit_tests_py2(run_slow_tests)


    def _increment_version(self):
        # Increment the version number
        self.version = increment_version(r"{}\__init__.py".format(app_name), app_name, format='increment')

    def _cleanup_last_build(self):
        # Cleanup last build
        if (self.topdir / 'dist').is_dir():
            shutil.rmtree(self.topdir / 'dist')
        if(self.topdir / 'build').is_dir():
            shutil.rmtree(self.topdir / 'build')

    def _create_build_copies(self):
        # Copy existing code into python 3 and 2 folders
        (self.topdir / 'build').mkdir()
        (self.topdir / 'build' / 'py3').mkdir()
        (self.topdir / 'build' / 'py2').mkdir()
        self._copy_to_build(self.topdir / 'build' / 'py2', py2=True)
        self._copy_to_build(self.topdir / 'build' / 'py3', py2=False)

    def _copy_to_build(self, output_dir: Path, py2=False):
        for root, dirs, files in os.walk(self.topdir.str):
            if 'build' in root:
                continue
            if '.git' in root:
                continue
            if '.idea' in root:
                continue
            if '__pycache__' in root:
                continue
            ext_dir = output_dir / Path(root).relative_to(self.topdir)
            if not ext_dir.is_dir():
                ext_dir.mkdir()
            for fn in files:
                if not (fn.endswith(".py") or fn.endswith(".txt")):
                    continue
                fp = Path(root) / fn
                ext = fp.relative_to(self.topdir)

                if fn.endswith(".py2.py"):
                    # Overwite the py3 version with py2
                    py3fn = output_dir / ext.str.replace(".py2.py", ".py")
                    assert py3fn.is_file(), f"Missing: {py3fn}"

                    if py2:
                        shutil.copy(fp, os.path.join(output_dir, ext.str.replace(".py2.py", ".py")))
                    else:
                        pass # noop: skip file
                else:
                    shutil.copy(fp, os.path.join(output_dir, ext.str))


    def _transpile_py2(self):
        # Run 3to6 on py2 folder
        from lib3to6.common import  BuildContext, BuildConfig, CheckError
        from lib3to6.transpile import transpile_module_data

        cfg = BuildConfig(target_version='2.7',
                          cache_enabled=False,
                          default_mode='enabled',
                          fixers=['AnnotationsFutureFixer', 'GeneratorStopFutureFixer',
                                    'UnicodeLiteralsFutureFixer', 'RemoveUnsupportedFuturesFixer',
                                    'PrintFunctionFutureFixer', 'WithStatementFutureFixer',
                                    'AbsoluteImportFutureFixer', 'DivisionFutureFixer',
                                    'GeneratorsFutureFixer', 'NestedScopesFutureFixer',
                                    'XrangeToRangeFixer',
                                    'UnicodeToStrFixer', 'UnichrToChrFixer', 'RawInputToInputFixer',
                                    'RemoveFunctionDefAnnotationsFixer', 'ForwardReferenceAnnotationsFixer',
                                    'RemoveAnnAssignFixer', 'ShortToLongFormSuperFixer',
                                    'InlineKWOnlyArgsFixer', 'NewStyleClassesFixer',
                                    'UnpackingGeneralizationsFixer',
                                    'NamedTupleClassToAssignFixer', 'FStringToStrFormatFixer',
                                    'UnpackingGeneralizationsFixer'],
                          checkers=['NoAsyncAwait', 'NoComplexNamedTuple',
                                    'NoYieldFromChecker', 'NoMatMultOpChecker'],
                          install_requires=None)
        for filepath in (self.topdir / 'build' / 'py2' / 'pjmlib').walk_files():
            if filepath.suffix != '.py':
                continue
            with open(filepath, mode='rb') as fobj:
                module_source_data = fobj.read()

            ctx = BuildContext(cfg, str(filepath))
            try:
                fixed_module_source_data = transpile_module_data(ctx,
                                                                 module_source_data)
            except CheckError as err:
                loc = str(filepath)
                if err.lineno >= 0:
                    loc += '@' + str(err.lineno)
                err.args = (loc + ' - ' + err.args[0],) + err.args[1:]
                raise
            with open(filepath, mode='wb') as fobj:
                fobj.write(fixed_module_source_data)

    def _run_unit_tests_py2(self, run_slow_tests):
        (self.topdir / 'build' / 'py2').chdir()
        os.environ['SLOW_TESTS'] = 'yes' if run_slow_tests else 'no'
        # os.system(r"C:\Personal\projects\venvs\venv_pjmlib_py27\Scripts\python.exe -m pjmlib.test_pjmlib")
        os.system(r"C:\Python27\python.exe -m unittest discover "
                  rf"-s {self.topdir / 'pjmlib' / 'tests'}"
                  rf"-t {self.topdir / 'pjmlib' / 'tests'}")

        print('-' * 80)
        print("Did the tests pass?")
        input(">>>")

    def _build_wheels(self):
        if self.version is None:
            from pjmlib import __version__
            self.version = __version__

        (self.topdir / 'dist').mkdir()

        (self.topdir / 'build' / 'py3').chdir()
        print("building py3 wheel...")
        os.system('python.exe setup.py sdist bdist_wheel')
        shutil.copy(self.topdir / 'build' / 'py3' / 'dist' / f"{app_name}-{self.version}-py3-none-any.whl",
                    self.topdir / 'dist')

        (self.topdir / 'build' / 'py2').chdir()
        print("building py2 wheel...")
        os.system('C:\Python27\python.exe setup.py sdist bdist_wheel')
        shutil.copy(self.topdir / 'build' / 'py2' / 'dist' / f"{app_name}-{self.version}-py2-none-any.whl",
                    self.topdir / 'dist')


    def _upload_to_nexus(self):
        (self.topdir / 'dist').chdir()
        push_to_nexus(r"{}-{}-py2-none-any.whl".format(app_name, self.version))
        push_to_nexus(r"{}-{}-py3-none-any.whl".format(app_name, self.version))

        (self.topdir / 'build').rmdir()

        print('')
        print('*'*80)
        print('* {} version {} has been built and uploaded to nexus.'.format(app_name, self.version))
        print('*'*80)

        print('')
        print('Next steps:')
        print(' 1. Update CHANGELOG.md')
        print(' 2. Commit to git and push.')

if __name__ == '__main__':
    builder = PjmlibBuilder()
    #builder.run_py2_tests(run_slow_tests=True)
    builder.run_full_build_cycle(run_test=True)