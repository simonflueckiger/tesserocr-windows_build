# tesserocr - Windows Build
[![Build status](https://ci.appveyor.com/api/projects/status/6po73amxb74q7nf3?svg=true)](https://ci.appveyor.com/project/simonflueckiger/tesserocr-windows-build)
[![Anaconda-Server Badge](https://anaconda.org/simonflueckiger/tesserocr/badges/version.svg)](https://anaconda.org/simonflueckiger/tesserocr) [![Anaconda-Server Badge](https://anaconda.org/simonflueckiger/tesserocr/badges/downloads.svg)](https://anaconda.org/simonflueckiger/tesserocr)
<br />![Supported python versions](https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)

This is the home of the Windows Python wheels for the official [**tesserocr**](https://github.com/sirfz/tesserocr) repository. The wheels come bundled with all the shared libraries necessary to execute **tesserocr**, 100% hassle-free. This means no tedious setting up of Tesseract and its dependencies.

You can download the wheel corresponding to your Python version from the [Releases](https://github.com/simonflueckiger/tesserocr-windows_build/releases) and install it via pip

```cmd
pip install <package_name>.whl
```

It's even more straightforward if you have conda installed

```cmd
conda install -c simonflueckiger tesserocr
```

## :warning: Prerequisites (tessdata)

Unfortunately, you won't get around a minimal amount of additional setup before using **tesserocr**. Make sure to download [tessdata](https://github.com/tesseract-ocr/tessdata) to a convenient location. Additionally, you have to either create an environment variable `TESSDATA_PREFIX` pointing to the location of tessdata or pass the path directly when initializing **tesserocr** as follows 

```python
PyTessBaseAPI(path='C:\path\to\tessdata')
```

Check out [tesserocr#tessdata](https://github.com/sirfz/tesserocr#tessdata) for more information.

## Python Versions
As a short disclaimer: I will only build packages targeting Python versions which are still actively supported (have not yet reached [EOL](https://endoflife.date/python) status). **This means I can't follow up on requests for Python versions 2.x or anything <= 3.6.**
