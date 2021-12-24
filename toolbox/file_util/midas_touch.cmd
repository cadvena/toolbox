@ echo off

set "target_folder=C:\Personal\Workspace"
set PYTHON="C:\ProgramData\Anaconda3\python.exe"
# TODO: fix path
set PY_SCRIPT_FOLDER="C:\Personal\Workspace\Code\Python\tsdlib\tsdlib\file_util"
set PY_SCRIPT="midas_touch.py"

echo Initializing Python Script...
cd %PY_SCRIPT_FOLDER%

:: %PYTHON% %PY_SCRIPT% --days 120 --recursive TRUE --folder "%target_folder%"
%PYTHON% %PY_SCRIPT% %1 %2 %3 %4 %5 %6 %7 %8 %9

::
:: Syntax:
::  midas_touch.cmd --days 120 --recursive TRUE --folder "%target_folder%"
::
::  where
::      --days (int): only files older than today minus days will we touched.
::      --folder (str): the target folder in which to run
::      --recursive (True/False): recurse through sub-folders