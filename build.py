import shutil
import os

from pjmlib.build_tools import increment_version, push_to_nexus

app_name = 'toolbox'

# Increment the version number
version = increment_version(r"{}\__init__.py".format(app_name), app_name)

# Cleanup last build
if os.path.isdir(r'dist'):
    shutil.rmtree(r'dist')


# Call setup.py to build the wheel and source
os.system('C:\Python27\python.exe setup.py sdist bdist_wheel --universal')

# Cleanup stuff left by build processes
shutil.rmtree('build')
shutil.rmtree('pjmlib.egg-info')


# Upload to nexus using twine
push_to_nexus(r"dist\{}-{}-py2.py3-none-any.whl".format(app_name, version))

print('')
print('*'*80)
print('* {} version {} has been built and uploaded to nexus.'.format(app_name, version))
print('*'*80)
