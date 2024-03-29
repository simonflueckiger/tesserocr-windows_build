import logging
import sys
import os
import shutil
import codecs
import re
import subprocess
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


def major_version(version):
    versions = version.split('.')
    major = int(versions[0])
    _LOGGER.info('Tesseract major version %s', major)
    return major


def version_to_int(version):
    subversion = None
    subtrahend = 0
    # Subtracts a certain amount from the version number to differentiate
    # between alpha, beta and release versions.
    if 'alpha' in version:
        version_split = version.split('alpha')
        subversion = version_split[1]
        subtrahend = 2
    elif 'beta' in version:
        version_split = version.split('beta')
        subversion = version_split[1]
        subtrahend = 1

    version = re.search(r'((?:\d+\.)+\d+)', version).group()
    # Split the groups on ".", take only the first one, and print each
    # group with leading 0 if needed. To be safe, also handle cases where
    # an extra group is added to the version string, or if one or two
    # groups are dropped.
    version_groups = (version.split('.') + [0, 0])[:3]
    version_str = '{:02}{:02}{:02}'.format(*map(int, version_groups))
    version_str = str((int(version_str, 10) - subtrahend))
    # Adds a 2 digit subversion number for the subversionrelease.
    subversion_str = '00'
    if subversion is not None and subversion != '':
        subversion = re.search(r'(?:\d+)', subversion).group()
        subversion_groups = (subversion.split('-') + [0, 0])[:1]
        subversion_str = '{:02}'.format(*map(int, subversion_groups))

    version_str += subversion_str
    return int(version_str, 16)


def find_dll_dependencies_recursively(dll_path, search_paths):
    dumpbin = subprocess.run(['dumpbin.exe', '/dependents', dll_path], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dependency_names = re.findall(r'^\s{4}(\S*\.dll)$', dumpbin.stdout, re.MULTILINE)

    dependencies = []
    for dependency_name in dependency_names:
        for search_path in search_paths:
            dependency_direct_full_path = os.path.join(search_path, dependency_name)
            if os.path.isfile(dependency_direct_full_path):
                dependencies.append(dependency_direct_full_path)
                break

    dependencies_recursive = []
    for dependency_direct_full_path in dependencies:
        dependencies_recursive.extend(find_dll_dependencies_recursively(dependency_direct_full_path, search_paths))

    dependencies.extend(dependencies_recursive)

    return list(set(dependencies))


def find_libraries(library_stems, search_paths, extension):
    library_paths = []

    for library_stem in library_stems:
        library = []
        for search_path in search_paths:
            library.extend([{ "filename": filename, "base_path": search_path} for filename in os.listdir(search_path) if re.search(r"^(?:lib)?{}(?:-(?:\d+\.)*|\d+\.|\.){}$".format(library_stem, extension), filename)])
        assert len(library) > 0, f"no libraries found in {search_paths} which match \"{library_stem}\" stem"
        assert len(library) == 1, f"multiple libraries found in which match \"{library_stem}\" stem:\n{library}"
        library_paths.append(os.path.join(library[0]["base_path"], library[0]["filename"]))

    return library_paths


class my_build_ext(build_ext, object):
    def initialize_options(self):
        build_ext.initialize_options(self)

        self.cython_compile_time_env = {
            'TESSERACT_VERSION': tesseract_version_int,
            'TESSERACT_MAJOR_VERSION': tesseract_version_major
        }
        self.extra_compile_args = [
            '/std:c11',
            '-DUSE_STD_NAMESPACE'
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
BUILD_PLATFORM = get_environment_variable('BUILD_PLATFORM')
INCLUDE_PATHS = get_environment_variable('INCLUDE_PATHS').split(';')
LIB_PATHS = get_environment_variable('LIB_PATHS').split(';')
DLL_PATHS = get_environment_variable('DLL_PATHS').split(';')

# parse tesseract version
tesseract_version_int = version_to_int(TESSERACT_VERSION)
tesseract_version_major = major_version(TESSERACT_VERSION)
_LOGGER.info(f"Tesseract version {TESSERACT_VERSION} converted to {tesseract_version_int} int representation")

build_dependencies = [
    "tesseract",
    "leptonica"
]

runtime_library_paths = find_libraries(["tesseract"], DLL_PATHS, "dll")
runtime_library_paths.extend(find_dll_dependencies_recursively(runtime_library_paths[0], DLL_PATHS))
_LOGGER.info("runtime libraries found:\n\t{}".format("\n\t".join(runtime_library_paths)))

build_dependency_paths = find_libraries(build_dependencies, LIB_PATHS, "lib")
_LOGGER.info("build dependencies found:\n\t{}".format("\n\t".join(build_dependency_paths)))
build_dependency_names = [os.path.splitext(os.path.basename(library_path))[0] for library_path in build_dependency_paths]

ext_modules = [
    ExtensionWithDLL(
        name="tesserocr._tesserocr",
        sources=["tesserocr.pyx"],
        language='c++',
        include_dirs=INCLUDE_PATHS,
        library_dirs=LIB_PATHS,
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
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
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
    setup_requires=['Cython>=0.23,<3.0.0', 'wheel']
)
