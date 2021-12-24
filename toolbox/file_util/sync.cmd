@echo off
set PYTHON="C:\ProgramData\Anaconda3\python.exe"
set PYSCRIPT="sync.py"
@echo on
%PYTHON% %PYSCRIPT% %1 %2 %3 %4 %5 %6 %7 %8 %9

@echo off
:: Syntax
:: sync config_file [output_file]
:: config_file format is csv with 3 columns: operation, source_folder, target_folder
:: valid values for operation: mirror, backup
