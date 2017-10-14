set TIMEZONE_PATCH=1
set BUILD_TARGET_32=1

rem set PATH=C:\Miniconda;C:\Miniconda\Scripts;%PATH%
rem conda install Cython PyYAML --yes
rem python setup.py bdist_wheel

rem set TIMEZONE_PATCH=0

set PATH=C:\Miniconda35;C:\Miniconda35\Scripts;%PATH%
conda install Cython PyYAML --yes
python setup.py bdist_wheel

set TIMEZONE_PATCH=0

set PATH=C:\Miniconda36;C:\Miniconda36\Scripts;%PATH%
conda install Cython PyYAML --yes
python setup.py bdist_wheel