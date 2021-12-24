"""

1. Update version and build timestamp in __init__.py

2. Update/regenerate requirements.txt if needed
    command: pip freeze > requirements_new.txt
    note: to install requirements, an-end user
          can run: pip install -r requirements.txt

2. If not done already, commit changes to pjm.git.com
   Be sure to include version number in commit notes.

3. Build toolbox wheel.  Open terminal:
    1st time setup:
        pip install buildtools
        pip install setuptools
        pip install wheel

    Each build:
        a. activate the venv for this project
        b. From terminal: python setup.py sdist bdist_wheel
            C:\Personal\Projects\toolbox\dist

4. Verify new dist created in "dist" folder

5. go to nexus.pjm.com, sign-in, and go to the public-pypi-hosted to upload.

Reference:
A setuptools based setup module:
    https://packaging.python.org/guides/distributing-packages-using-setuptools/
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib
import toolbox
import inspect
import os

# Get info from text files
here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')
license_txt = (here / 'LICENSE.txt').read_text(encoding='utf-8')
version = toolbox.__version__

current_fp = inspect.stack()[0][1]
current_dir = os.path.dirname(current_fp)

setup(
    name='toolbox',
    author='Christopher J. Advena',
    author_email='chris.advena@pjm.com',
    version=version,
    packages = find_packages(),
    install_requires=open(os.path.join(current_dir, 'requirements.txt')).readlines(),
    package_data={
                  'toolbox': ['*.config', '*.ini', 'file_util/*.cmd', 'img/*.png'],
                  'cookbook': ['*.cmd']
                 },

    python_requires='>=3.6, <4',
    description=long_description,
    # long_description_content_type='text/markdown',
    url='https://git.pjm.com/transmission-service-department/toolbox',
    # project_urls={
    #     'source': 'https://git.pjm.com/transmission-service-department/toolbox',
    #     'distribution': 'https://nexus.pjm.com/nexus/#browse/browse:public-pypi-hosted:toolbox'},

        # Classifiers help users find your project by categorizing it.
        # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers = [  # Optional
                      # How mature is this project? Common values are
                      #   3 - Alpha
                      #   4 - Beta
                      #   5 - Production/Stable
                      'Development Status :: 5 - Production/Stable',

                      # Indicate who your project is intended for
                      'Intended Audience :: Developers',
                      'Topic :: Software Development :: Python Tools',

                      # Pick your license as you wish
                      'License :: OSI Approved :: MIT License',

                      # Specify the Python versions you support here. In particular, ensure
                      # that you indicate you support Python 3. These classifiers are *not*
                      # checked by 'pip install'. See instead 'python_requires' below.
                      'Programming Language :: Python :: 3',
                      'Programming Language :: Python :: 3.7',
                      'Programming Language :: Python :: 3.8',
                      'Programming Language :: Python :: 3.9',
                      'Programming Language :: Python :: 3.10',
                      'Programming Language :: Python :: 3 :: Only',
                      ],
)