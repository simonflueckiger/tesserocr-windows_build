rem PATH=C:\Miniconda;C:\Miniconda\Scripts;%PATH%
rem pip install tesserocr\dist\tesserocr-2.2.2-cp27-cp27m-win32.whl
rem conda install Pillow --yes
rem python tesserocr\tests\test_api.py

PATH=C:\Miniconda35;C:\Miniconda35\Scripts;%PATH%
pip install tesserocr\dist\tesserocr-2.2.2-cp35-cp35m-win32.whl
conda install Pillow --yes
python tesserocr\tests\test_api.py

PATH=C:\Miniconda36;C:\Miniconda36\Scripts;%PATH%
pip install tesserocr\dist\tesserocr-2.2.2-cp36-cp36m-win32.whl
conda install Pillow --yes
python tesserocr\tests\test_api.py