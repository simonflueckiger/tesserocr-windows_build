import logging
import sys
import os
import shutil
import codecs
import re
from distutils.util import strtobool
import setuptools  # needed for bdist_wheel
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext


# ------ setup logger
_LOGGER = logging.getLogger()
if strtobool(os.environ.get('DEBUG', '0')):
    _LOGGER.setLevel(logging.DEBUG)
else:
    _LOGGER.setLevel(logging.INFO)
_LOGGER.addHandler(logging.StreamHandler(sys.stderr))


def get_environment_variable(name):
    value = os.environ.get(name)
    assert value, f"environment variable {name} not set"
    return value


def read(*parts):
    here = os.path.abspath(os.path.dirname(__file__))
    return codecs.open(os.path.join(here, *parts), 'r').read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


def find_libraries(library_stems, search_path, extension):
    library_paths = []

    for lib_stem in library_stems:
        library_filename = [filename for filename in os.listdir(search_path) if re.search(r"^{}[-\.\d]+.*{}$".format(lib_stem, extension), filename)]
        assert len(library_filename) == 1, f"multiple runtime libraries found in {search_path} which match \"{lib_stem}\" stem"
        library_paths.append(os.path.join(search_path, library_filename[0]))

    return library_paths


class my_build_ext(build_ext, object):
    def initialize_options(self):
        build_ext.initialize_options(self)

        self.cython_compile_time_env = {
            'TESSERACT_VERSION': 67174912,
            'TESSERACT_MAJOR_VERSION': 4
        }
        self.extra_compile_args = [
            '-std=c++11'
        ]

    def build_extension(self, ext):
        assert (isinstance(ext, ExtensionWithDLL))

        if hasattr(ext, 'dlls'):
            dll_dest_dir = os.path.dirname(self.get_ext_fullpath(ext.name))
            for dll_name_pattern in ext.dlls:
                dll_src_dir, dll_name = os.path.split(dll_name_pattern)
                if dll_name == '*.dll':
                    raise NotImplemented('not implemented')
                else:
                    if os.path.isabs(dll_name_pattern):
                        try:
                            os.makedirs(dll_dest_dir, exist_ok=True)
                            shutil.copy(dll_name_pattern, dll_dest_dir)

                            pass
                        except shutil.SameFileError:
                            pass
                        except:
                            raise
                    else:
                        # todo: handle relative paths
                        raise NotImplementedError('not implemented')

        return build_ext.build_extension(self, ext)


class ExtensionWithDLL(Extension):
    def __init__(self, name, sources, *args, **kw):
        self.dlls = kw.pop("dlls", [])
        Extension.__init__(self, name, sources, *args, **kw)


# get environment variables
TESSERACT_VERSION = get_environment_variable('TESSERACT_VERSION')
VCPKG_PATH = get_environment_variable('VCPKG_PATH')
BUILD_PLATFORM = get_environment_variable('BUILD_PLATFORM')

vcpkg_bin = Rf"{VCPKG_PATH}\installed\{BUILD_PLATFORM}-windows\bin"
vcpkg_lib = Rf"{VCPKG_PATH}\installed\{BUILD_PLATFORM}-windows\lib"
vcpkg_include = Rf"{VCPKG_PATH}\installed\{BUILD_PLATFORM}-windows\include"

build_dependencies = [
    "tesseract",
    "leptonica"
]

# indentations with respect to dependency
runtime_libraries = [
    "tesseract",
        "leptonica",
            "gif",
            "jpeg",
            "libpng",
            "zlib",
            "tiff",
                "lzma",
            "libwebpmux",
            "webp"
]


runtime_library_paths = find_libraries(runtime_libraries, vcpkg_bin, "dll")
_LOGGER.info("runtime libraries found:\n\t{}".format("\n\t".join(runtime_library_paths)))

build_dependency_paths = find_libraries(build_dependencies, vcpkg_lib, "lib")
_LOGGER.info("build dependencies found:\n\t{}".format("\n\t".join(build_dependency_paths)))
build_dependency_names = [os.path.splitext(os.path.basename(library_path))[0] for library_path in build_dependency_paths]

ext_modules = [
    ExtensionWithDLL(
        name="tesserocr._tesserocr",
        sources=["tesserocr.pyx"],
        language='c++',
        include_dirs=[
            vcpkg_include
        ],
        library_dirs=[
            vcpkg_lib
        ],
        libraries=build_dependency_names,
        dlls=runtime_library_paths
    )
]

setup(
    name='tesserocr',
    version=find_version('tesserocr.pyx'),
    description='A simple, Pillow-friendly, Python wrapper around '
                'tesseract-ocr API using Cython',
    long_description=read('README.rst'),
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
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Cython',
    ],
    keywords='Tesseract,tesseract-ocr,OCR,optical character recognition,'
             'PIL,Pillow,Cython',

    cmdclass={'build_ext': my_build_ext},
    ext_modules=ext_modules,
    packages=['tesserocr'],
    test_suite='tests',
    setup_requires=['Cython>=0.23', 'wheel']
)
