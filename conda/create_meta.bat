echo package: > meta.yaml
echo     name: tesserocr >> meta.yaml
echo     version: %TESSEROCR_VER% >> meta.yaml
echo build: >> meta.yaml
echo   number: %BUILD_NUMBER% >> meta.yaml
echo   string: tesseract_%TESSERACT_VER%_%BUILD_NUMBER% >> meta.yaml
echo requirements: >> meta.yaml
echo   build: >> meta.yaml
echo     - python >> meta.yaml
echo   run: >> meta.yaml
echo     - python >> meta.yaml
echo about: >> meta.yaml
echo     home: https://github.com/sirfz/tesserocr >> meta.yaml
echo     license: MIT >> meta.yaml
echo     summary: A simple, Pillow-friendly, Python wrapper around tesseract-ocr API using Cython >> meta.yaml
