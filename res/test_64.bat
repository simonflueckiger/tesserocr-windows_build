rem PATH=C:\Miniconda-x64;C:\Miniconda-x64\Scripts;%PATH%
rem pip install tesserocr\dist\tesserocr-2.2.2-cp27-cp27m-win_amd64.whl
rem conda install Pillow --yes
rem python tesserocr\tests\test_api.py

rem PATH=C:\Miniconda35-x64;C:\Miniconda35-x64\Scripts;%PATH%
rem pip install tesserocr\dist\tesserocr-2.2.2-cp35-cp35m-win_amd64.whl
rem conda install Pillow --yes
rem python tesserocr\tests\test_api.py

PATH=C:\Miniconda36-x64;C:\Miniconda36-x64\Scripts;%PATH%
pip install tesserocr\dist\tesserocr-2.2.2-cp36-cp36m-win_amd64.whl
conda install Pillow --yes
python tesserocr\tests\test_api.py

PATH=C:\Miniconda37-x64;C:\Miniconda37-x64\Scripts;%PATH%
pip install tesserocr\dist\tesserocr-2.2.2-cp37-cp37m-win_amd64.whl
conda install Pillow --yes
python tesserocr\tests\test_api.py
