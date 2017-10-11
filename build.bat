copy res\setup.py tesserocr\setup.py
xcopy /s res\tesserocr tesserocr\tesserocr\
cd tesserocr
python setup.py install
python tests\test_api.py