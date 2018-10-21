(
echo package:
echo     name: tesserocr
echo     version: %$TESSEROCR_VER%
echo build:
echo   number: %$BUILD_NUMBER%
echo   string: tesseract_%$TESSERACT_VER%_%$BUILD_NUMBER%
echo requirements:
echo   build:
echo     - python  
echo   run:
echo     - python
echo about:
echo     home: https://github.com/sirfz/tesserocr
echo     license: MIT
echo     summary: A simple, Pillow-friendly, Python wrapper around tesseract-ocr API using
echo         Cython
) > meta.yaml
