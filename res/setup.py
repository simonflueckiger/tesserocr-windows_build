from setuptools import setup, find_packages
from setuptools.extension import Extension
from setuptools.command.build_ext import build_ext
from Cython.Build import cythonize
from glob import glob
import distutils.sysconfig
import os
import re
import codecs
from os.path import join as pjoin
from os.path import dirname, abspath

# find_version from pip https://github.com/pypa/pip/blob/1.5.6/setup.py#L33
here = abspath(dirname(__file__))

def read(*parts):
    return codecs.open(pjoin(here, *parts), 'r').read()

def version_to_int(version):
    subversion = None
    subtrahend = 0
    # Subtracts a certain amount from the version number to differentiate between
    # alpha, beta and release versions.
    if "alpha" in version:
        version_split = version.split("alpha")
        subversion = version_split[1]
        subtrahend = 2
    elif "beta" in version:
        version_split = version.split("beta")
        subversion = version_split[1]
        subtrahend = 1
    version = re.search(r'((?:\d+\.)+\d+)', version).group()
    # Split the groups on ".", take only the first one, and print each group with leading 0 if needed
    # To be safe, also handle cases where an extra group is added to the version string, or if one or two groups
    # are dropped.
    version_groups = (version.split('.') + [0, 0])[:3]
    version_str = "{:02}{:02}{:02}".format(*map(int, version_groups))
    version_str = str((int(version_str, 10)-subtrahend))
    # Adds a 2 digit subversion number for the subversionrelease.
    subversion_str="00"
    if subversion is not None and subversion != "":
        subversion = re.search(r'(?:\d+)', subversion).group()
        subversion_groups = (subversion.split('-') + [0, 0])[:1]
        subversion_str = "{:02}".format(*map(int, subversion_groups))
    version_str+=subversion_str
    return int(version_str, 16)

ext_module_dostuff = Extension(
    "tesserocr",
    sources=["tesserocr.pyx"],
    language="c++",
    include_dirs=[
        R"C:/Tools/vcpkg/installed/x64-windows/include",
        R"C:/projects/tesserocr-windows-cmake/tesseract/include",
    ],
    libraries=["leptonica-1.78.0", "tesseract41"],
    library_dirs=[
        # tesseract .lib import library
        R"C:/projects/tesserocr-windows-cmake/tesseract/build/Release",

        # leptonica (and deps) .lib import libraries
        R"C:/Tools/vcpkg/installed/x64-windows/lib"
    ]
)

setup(
    name="tesserocr",
    version="2.5.1",
    description='A simple, Pillow-friendly, Python wrapper around tesseract-ocr API using Cython',
    long_description=read(R"README.rst"),
    long_description_content_type='text/x-rst',
    url='https://github.com/sirfz/tesserocr',
    author='Fayez Zouheiry',
    author_email='iamfayez@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Multimedia :: Graphics :: Capture :: Scanners',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Cython'
    ],
    keywords='Tesseract,tesseract-ocr,OCR,optical character recognition,PIL,Pillow,Cython',
    ext_modules=cythonize(
        ext_module_dostuff,
        compile_time_env={'TESSERACT_VERSION': version_to_int("04.01.00")},
        language="c++"
    ),
    setup_requires=['Cython>=0.23']
)