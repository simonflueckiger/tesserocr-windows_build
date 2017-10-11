copy res\setup.py tesserocr\setup.py
xcopy /s res\tesserocr tesserocr\tesserocr\
cd tesserocr
python setup.py bdist_wheel
cd ..