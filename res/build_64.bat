set TIMEZONE_PATCH=1
set BUILD_TARGET_32=0

rem set PATH=C:\Miniconda-x64;C:\Miniconda-x64\Scripts;%PATH%
rem conda install Cython PyYAML --yes
rem python setup.py bdist_wheel

rem set TIMEZONE_PATCH=0

rem set PATH=C:\Miniconda35-x64;C:\Miniconda35-x64\Scripts;%PATH%
rem conda install Cython PyYAML --yes
rem python setup.py bdist_wheel

set TIMEZONE_PATCH=1

PATH=C:\Miniconda36-x64;C:\Miniconda36-x64\Scripts;%PATH%
conda install Cython PyYAML --yes
python setup.py bdist_wheel

set TIMEZONE_PATCH=1

PATH=C:\Miniconda37-x64;C:\Miniconda37-x64\Scripts;%PATH%
conda install Cython PyYAML --yes
python setup.py bdist_wheel
