import logging
import os
import sys
import codecs
import re
import subprocess
import errno
from os.path import dirname, abspath
from os.path import split as psplit, join as pjoin
from setuptools import setup, Extension
from Cython.Distutils import build_ext
from distutils.util import strtobool

_LOGGER = logging.getLogger()
if strtobool(os.environ.get('DEBUG', '0')):
    _LOGGER.setLevel(logging.DEBUG)
else:
    _LOGGER.setLevel(logging.INFO)
_LOGGER.addHandler(logging.StreamHandler(sys.stderr))

_TESSERACT_MIN_VERSION = '3.04.00'

# find_version from pip https://github.com/pypa/pip/blob/1.5.6/setup.py#L33
here = abspath(dirname(__file__))


def go_up(dir, n):
    if n == 0:
        return dir

    return os.path.dirname(go_up(dir, n-1))


def apply_patches():
    dirty_bit = False

    _LOGGER.info("\nPatching timezone naming conflict...\n------------------------------------")

    def find(name, path):
        for root, dirs, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)

    def find_all(name, path):
        result = []
        for root, dirs, files in os.walk(path):
            if name in files:
                result.append(os.path.join(root, name))
        return result


    if strtobool(os.environ.get('TIMEZONE_PATCH', '0')) and not strtobool(os.environ.get('SKIP_TIMEZONE_PATCH', '0')):
        dirty_bit = True

        home_dir = os.environ.get('USERPROFILE')
        header_path = find("gettimeofday.h", home_dir + r"\.cppan\storage\src")
        source_path = os.path.dirname(header_path)
        h_path = source_path + '\gettimeofday.h'
        cpp_path = source_path + '\gettimeofday.cpp'

        with open(h_path, 'r+') as fp:
            _LOGGER.info("patching {}".format(h_path))
            contents = fp.read()
            contents = contents.replace('timezone', 'not_used_timezone')
            fp.truncate(0)
            fp.seek(0)
            fp.write(contents)

        with open(cpp_path, 'r+') as fp:
            _LOGGER.info("patching {}".format(cpp_path))
            contents = fp.read()
            contents = contents.replace('timezone', 'not_used_timezone')
            fp.truncate(0)
            fp.seek(0)
            fp.write(contents)


    # patch unichar.h, unichar.cpp, unicharset.h, unicharset.cpp
    # this should be redundant for builds past commit ad6f3b412a9a18f3819ae9feaf872464c7bf0e7b when string was
    # changed to std::string
    if strtobool(os.environ.get('STRING_PATCH', '0')):
        dirty_bit = True

        for type in [".h", ".cpp"]:
            unichar_path_from = "../res/patch/unichar" + type
            unichar_path_to = go_up(source_path, 2) + r"\ccutil\unichar" + type
            _LOGGER.info("patching {}".format(unichar_path_to))
            shutil.copy(unichar_path_from, unichar_path_to)

            unicharset_path_from = "../res/patch/unicharset" + type
            unicharset_path_to = go_up(source_path, 2) + r"\ccutil\unicharset" + type
            _LOGGER.info("patching {}".format(unicharset_path_to))
            shutil.copy(unicharset_path_from, unicharset_path_to)

    if dirty_bit:
        # delete lnk folder
        lnk_path = home_dir + "\.cppan\storage\lnk"
        _LOGGER.info("deleting {}".format(lnk_path))
        shutil.rmtree(lnk_path)

        # # delete obj file
        # obj_paths = find_all("gettimeofday.obj", home_dir + r"\.cppan\storage\obj")
        # for obj_path in obj_paths:
        #     os.remove(obj_path)
        #     _LOGGER.info("removed {}".format(obj_path))

        # delete obj folder
        obj_folder_path = home_dir + "\.cppan\storage\obj"
        _LOGGER.info("deleting {}".format(obj_folder_path))
        shutil.rmtree(obj_folder_path)

    _LOGGER.info("------------------------------------\n")

    return dirty_bit

def read(*parts):
    return codecs.open(pjoin(here, *parts), 'r').read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


if sys.version_info >= (3, 0):
    def _read_string(s):
        return s.decode('UTF-8')
else:
    def _read_string(s):
        return s


def version_to_int(version):
    version = re.search(r'((?:\d+\.)+\d+)', version).group()
    return int(''.join(version.split('.')), 16)


def package_config():
    """Use pkg-config to get library build parameters and tesseract version."""
    p = subprocess.Popen(['pkg-config', '--exists', '--atleast-version={}'.format(_TESSERACT_MIN_VERSION),
                          '--print-errors', 'tesseract'],
                         stderr=subprocess.PIPE)
    output, error = p.communicate()
    _LOGGER.info(output)
    if p.returncode != 0:
        raise Exception(error)
    p = subprocess.Popen(['pkg-config', '--libs', '--cflags', 'tesseract'], stdout=subprocess.PIPE)
    output, _ = p.communicate()
    _LOGGER.info(output)
    flags = _read_string(output).strip().split()
    p = subprocess.Popen(['pkg-config', '--libs', '--cflags', 'lept'], stdout=subprocess.PIPE)
    output, _ = p.communicate()
    _LOGGER.info(output)
    flags2 = _read_string(output).strip().split()
    options = {'-L': 'library_dirs',
               '-I': 'include_dirs',
               '-l': 'libraries'}
    config = {}
    import itertools
    for f in itertools.chain(flags, flags2):
        try:
            opt = options[f[:2]]
        except KeyError:
            continue
        val = f[2:]
        if opt == 'include_dirs' and psplit(val)[1].strip(os.sep) in ('leptonica', 'tesseract'):
            val = dirname(val)
        config.setdefault(opt, set()).add(val)
    config = {k: list(v) for k, v in config.items()}
    p = subprocess.Popen(['pkg-config', '--modversion', 'tesseract'], stdout=subprocess.PIPE)
    version, _ = p.communicate()
    _LOGGER.info(version)
    version = _read_string(version).strip()
    _LOGGER.info("Supporting tesseract v{}".format(version))
    config['cython_compile_time_env'] = {'TESSERACT_VERSION': version_to_int(version)}
    _LOGGER.info("Configs from pkg-config: {}".format(config))
    return config

def get_tesseract_version():
    """Try to extract version from tesseract otherwise default min version."""
    config = {'libraries': ['tesseract', 'lept']}
    try:
        p = subprocess.Popen(['tesseract', '-v'], stderr=subprocess.PIPE)
        _, version = p.communicate()
        version = _read_string(version).strip()
        version_match = re.search(r'^tesseract ((?:\d+\.)+\d+).*', version, re.M)
        if version_match:
            version = version_match.group(1)
        else:
            _LOGGER.warning('Failed to extract tesseract version number from: {}'.format(version))
            version = _TESSERACT_MIN_VERSION
    except OSError as e:
        _LOGGER.warning('Failed to extract tesseract version from executable: {}'.format(e))
        version = _TESSERACT_MIN_VERSION
    _LOGGER.info("Supporting tesseract v{}".format(version))
    version = version_to_int(version)
    config['cython_compile_time_env'] = {'TESSERACT_VERSION': version}
    _LOGGER.info("Building with configs: {}".format(config))
    return config

class BuildTesseract(build_ext):
    """Set build parameters obtained from pkg-config if available."""

    def initialize_options(self):
        build_ext.initialize_options(self)

        try:
            build_args = package_config()
        except Exception as e:
            if isinstance(e, OSError):
                if e.errno != errno.ENOENT:
                    _LOGGER.warning('Failed to run pkg-config: {}'.format(e))
            else:
                _LOGGER.warning('pkg-config failed to find tesseract/lep libraries: {}'.format(e))
            build_args = get_tesseract_version()

        if build_args['cython_compile_time_env']['TESSERACT_VERSION'] >= 0x040000:
            _LOGGER.info('tesseract >= 4.00 requires c++11 compiler support')
            build_args['extra_compile_args'] = ['-std=c++11', '-DUSE_STD_NAMESPACE']

        _LOGGER.info('build parameters: {}'.format(build_args))
        for k, v in build_args.items():
            setattr(self, k, v)
            
    def build_extension(self, ext):
        if 0:
            assert(isinstance(ext, ExtensionWithDLL))
        if hasattr(ext, 'dlls'):
            dll_dest_dir = os.path.dirname(self.get_ext_fullpath(ext.name))
            for dll_name_pattern in ext.dlls:
                dll_src_dir, dll_name = os.path.split(dll_name_pattern)
                if dll_name == '*.dll':
                    raise NotImplemented('not implemented')
                else:
                    if os.path.isabs(dll_name_pattern):
                        try:
                            shutil.copy(dll_name_pattern, dll_dest_dir)
                        except shutil.SameFileError:
                            pass
                        except:
                            raise
                    else:
                        # how to handle relative path???
                        raise NotImplementedError('not implemented')
        
        return build_ext.build_extension(self, ext)

if sys.platform == 'win32':
    from distutils.util import get_platform
    import shutil
    import shlex
    import yaml

    tesseract_dll_files = []

    leptonica_version = os.environ.get('LEPTONICA_VERSION', '1.74.4')
    tesseract_version = os.environ.get('TESSERACT_VERSION', '3.5.1')

    def prepare_tesseract_env(leptonica_version=leptonica_version, tesseract_version=tesseract_version):
        global tesseract_dll_files
        top_dir = os.path.dirname(os.path.abspath(__file__))
        build_dir = os.path.join(top_dir, 'build', 'tesseract_build')
    
        # remove the old build directory
        if os.path.isdir(build_dir):
            shutil.rmtree(build_dir, ignore_errors=True)
        elif os.path.exists(build_dir):
            os.remove(build_dir)
    
        # create the empty build directory
        # os.makedirs(build_dir, exist_ok=True)
        os.makedirs(build_dir)
    
        # create dummy.cpp file
        with open(os.path.join(build_dir, 'dummy.cpp'), 'w') as fp:
            fp.write('int main(int argc, char *argv[]) { return 0; }\n')
    
        # create cppan.yml cppan configuration file

        generator = os.environ.get('GENERATOR_BASE', 'Visual Studio 15 2017')
        if get_platform() == 'win-amd64':
            if not strtobool(os.environ.get('BUILD_TARGET_32', '0')):
                _LOGGER.info('building for Win64')
                generator += ' Win64'
            else:
                _LOGGER.info('building for Win32')
        elif get_platform() == 'win32':
            _LOGGER.info('building for Win32')
        else:
            _LOGGER.error('platform not supported')

        _LOGGER.info('using {}'.format(generator))

        tesseract_major_version = int(tesseract_version[0])

        # if tesseract_major_version >= 4:
        #     tesseract_cppan_version = "master"
        # else:
        #     tesseract_cppan_version = tesseract_version

        tesseract_cppan_version = os.environ.get('CPPAN_TESSERACT_VERSION', tesseract_version)
    
        cppan_config = """
local_settings:
  cppan_dir: cppan
  build_dir_type: local
  build_dir: build
  build:
    generator: %s

projects:
  dummy:
    files: dummy.cpp
    dependencies:
      pvt.cppan.demo.danbloomberg.leptonica: %s
      pvt.simonflueckiger.tesseract.libtesseract: %s
      pvt.simonflueckiger.tesseract.tesseract: %s
""" % (generator, leptonica_version, tesseract_cppan_version, tesseract_cppan_version)
    
        with open(os.path.join(build_dir, 'cppan.yml'), 'w') as fp:
            fp.write(cppan_config)

        def build_tesseract_exe():
            # build tesseract.exe

            _LOGGER.info("tesseract version: {}".format(tesseract_version))
            _LOGGER.info("tesseract cppan version: {}".format(tesseract_cppan_version))

            cmd = 'cppan --build-packages pvt.simonflueckiger.tesseract.tesseract-%s' % tesseract_cppan_version

            # simonflueckiger: added a bit of verbosity to popen call
            p = subprocess.Popen(shlex.split(cmd), cwd=build_dir,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

            for stdout_line in iter(p.stdout.readline, ""):
                _LOGGER.debug(stdout_line.strip())
            p.stdout.close()
            return_code = p.wait()

            if return_code != 0:
                raise RuntimeError("something went wrong during cppan --build-packages")

        _LOGGER.info("building packages")
        build_tesseract_exe()
        _LOGGER.info("building packages done")


        if apply_patches():
            _LOGGER.info("rebuilding packages after patch")
            build_tesseract_exe()
            _LOGGER.info("rebuilding packages done")


        # build dummy.exe
        cmd = 'cppan --build .'
        _LOGGER.info("test_01")
        p = subprocess.Popen(shlex.split(cmd), cwd=build_dir,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        output = ""
        _LOGGER.info("test_02")
        for stdout_line in iter(p.stdout.readline, ""):
            output += stdout_line
            _LOGGER.debug(stdout_line.strip())
        p.stdout.close()
        return_code = p.wait()

        # output, err = p.communicate()

        _LOGGER.info("test_03")
        # _LOGGER.info(output.decode())
        _LOGGER.info("test_04")

        # simonflueckiger: added german success message check
        if output.find('Build succeeded.') < 0 and output.find('Buildvorgang wurde erfolgreich') < 0:
            raise RuntimeError(output.decode())
        _LOGGER.info("test_05")
    
        # figure out our configuration
        files = os.listdir(os.path.join(build_dir, 'bin'))
        _LOGGER.info("files: {}".format(files))
        dll_files = [name for name in files \
                     if os.path.isfile(os.path.join(build_dir, 'bin', name)) and \
                     name.endswith('.dll')]
        lib_files = [name for name in files if os.path.isfile(os.path.join(build_dir, 'bin', name)) and \
                                                              name.endswith('.lib')]
        tesseract_dll_files.extend([os.path.join(build_dir, 'bin', name) for name in dll_files])

        _LOGGER.info("tesseract_dll_files: {}".format(tesseract_dll_files))

        # get the tesseract version from executable
        cmd = '%s -v' % os.path.join(build_dir, 'bin', 'tesseract.exe')
        args = shlex.split(cmd, posix=False)
        p = subprocess.Popen(args, cwd=os.path.join(build_dir, 'bin'),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate()

        _LOGGER.info("trying to extract tesseract version")
        _LOGGER.info("version string: {}".format(output.decode()))

        if p.returncode != 0:
            raise RuntimeError('tesseract execution failed????')
        m = re.search("tesseract ([0-9]+\.[0-9]+\.[0-9]+)", output.decode())
        if m is None:
            raise RuntimeError('unknown tesseract version number???')
        tesseract_version = m.group(1)
        tesseract_version_number = int(''.join(tesseract_version.split('.')), 16)

        _LOGGER.info("extracted tesseract version from executable")
        _LOGGER.info("tesseract version: {}".format(tesseract_version))
        _LOGGER.info("tesseract version number: {}".format(tesseract_version_number))
    
        # prepare header files
        d = os.path.split(build_dir)[-1]
        dummy_build_dir = os.path.join(build_dir, 'build', 'cppan-build-%s' % d)
    
        # we should have only one subdir
        subdirs = [name for name in os.listdir(dummy_build_dir) \
                  if os.path.isdir(os.path.join(dummy_build_dir, name))]
        assert(len(subdirs) == 1)
        # the magic number, some kind of hash key, should be relate to architectures,
        # compiler selection, debug/release, etc ...
        magic_number = subdirs[0]
        dummy_build_dir = os.path.join(dummy_build_dir, subdirs[0])
        dummy_cmakefile = os.path.join(dummy_build_dir, 'cppan', 'CMakeLists.txt')
        with open(dummy_cmakefile, 'r') as fp:
            contents = fp.read()
    
        m = re.search(r"set\(pvt_cppan_[0-9a-zA-Z_]+leptonica_DIR (?P<dir>.+)\)",
                      contents)
        if not m:
            raise RuntimeError('cannot detect leptonica source codes')
        
        leptonica_top_dir = m.group('dir')
        leptonica_build_dir = leptonica_top_dir.replace('/src/','/obj/', 1)
        m = re.search('/[0-9a-fA-F]{2}/[0-9a-fA-F]{2}/[0-9a-fA-F]{4}$', leptonica_build_dir)
        if not m:
            raise RuntimeError('unexpected source location directory name')
        leptonica_hash = m.group(0).replace('/', '')
        leptonica_build_dir = os.path.normpath(os.path.join(leptonica_build_dir, 
                                                            'build', magic_number,
                                                            'cppan', leptonica_hash))
        leptonica_top_dir = os.path.normpath(leptonica_top_dir)
    
        m = re.search(r"set\(pvt_[0-9a-zA-Z_]+libtesseract_DIR (?P<dir>.+)\)",
                      contents)
        if not m:
            raise RuntimeError('cannot detect libtesseract source codes')
        libtesseract_src_dir = os.path.normpath(m.group('dir'))
    
        # copy header files from leptonica and libtesseract source tree
        os.makedirs(os.path.join(build_dir, 'include', 'leptonica'))
        os.makedirs(os.path.join(build_dir, 'include', 'tesseract'))
    
        leptonica_src_dir = os.path.join(leptonica_top_dir, 'src')
        leptonica_h_files = [name for name in os.listdir(leptonica_src_dir) \
                             if name.endswith('.h') and \
                             os.path.isfile(os.path.join(leptonica_src_dir, name))]
        for name in leptonica_h_files:
            shutil.copy(os.path.join(leptonica_src_dir, name),
                        os.path.join(build_dir, 'include', 'leptonica'))
    
        # take care of generated header files
        leptonica_h_files = [name for name in os.listdir(leptonica_build_dir) \
                             if name.endswith('.h') and \
                             os.path.isfile(os.path.join(leptonica_build_dir, name))]
        for name in leptonica_h_files:
            shutil.copy(os.path.join(leptonica_build_dir, name),
                        os.path.join(build_dir, 'include', 'leptonica'))
        
        # from libtesseract source tree
        with open(os.path.join(libtesseract_src_dir, 'cppan.yml'), 'r') as fp:
            cppan_cfg = yaml.load(fp)
            subdirs = cppan_cfg['include_directories']['public']
        
        for subdir in subdirs:
            subdir = os.path.normpath(os.path.join(libtesseract_src_dir, subdir))
            h_files = [name for name in os.listdir(subdir) \
                       if name.endswith('.h') and \
                       os.path.isfile(os.path.join(subdir, name))]
            
            for name in h_files:
                shutil.copy(os.path.join(subdir, name),
                            os.path.join(build_dir, 'include', 'tesseract'))

        # simonflueckiger: not needed anymore
        # # need to patch the gettimeofday.h
        # with open(os.path.join(build_dir, 'include', 'tesseract', 'gettimeofday.h'), 'r+') as fp:
        #     contents = fp.read()
        #     contents = contents.replace('timezone', 'not_used_timezone')
        #     fp.truncate(0)
        #     fp.seek(0)
        #     fp.write(contents)

        # copy all dll files to package directory
        # package_dir = os.path.join(top_dir, 'tesserocr')
        
        # remove old dll files
        # for dll in os.listdir(package_dir):
        #    if dll.endswith('.dll'):
        #        os.remove(os.path.join(package_dir, dll))
    
        # for dll in tesseract_dll_files:
        #     shutil.copy(dll, package_dir)
        
        config = {
            'library_dirs' : [os.path.join(build_dir, 'bin')],
            'include_dirs' : [os.path.join(build_dir, 'include')],
            'libraries'    : [os.path.splitext(lib)[0] for lib in lib_files],
            'cython_compile_time_env' : {'TESSERACT_VERSION': tesseract_version_number }   
        }

        _LOGGER.info("config: {}".format(config))

        return config
    
    package_config = prepare_tesseract_env
    
    class ExtensionWithDLL(Extension):
        def __init__(self, name, sources, *args, **kw):
            self.dlls = kw.pop("dlls", [])            
            Extension.__init__(self, name, sources, *args, **kw)

    
    ext_modules = [ExtensionWithDLL("tesserocr._tesserocr",
                                    sources=["tesserocr.pyx"],
                                    language="c++",
                                    dlls = tesseract_dll_files)]
    
    setup(name='tesserocr',
          version=find_version('tesserocr.pyx'),
          description='A simple, Pillow-friendly, Python wrapper around tesseract-ocr API using Cython',
          long_description=read('README.rst'),
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
              'Programming Language :: Python :: 3.2',
              'Programming Language :: Python :: 3.3',
              'Programming Language :: Python :: 3.4',
              'Programming Language :: Python :: 3.5',
              'Programming Language :: Python :: Implementation :: CPython',
              'Programming Language :: Python :: Implementation :: PyPy',
              'Programming Language :: Cython'
              ],
          keywords='Tesseract,tesseract-ocr,OCR,optical character recognition,PIL,Pillow,Cython',
          # cmdclass={'build_ext': CustomBuildExit},
          cmdclass={'build_ext': BuildTesseract},
          ext_modules=ext_modules,
          packages = ['tesserocr'],
          test_suite='tests'
          )

else:
    ext_modules = [Extension("tesserocr",
                             sources=["tesserocr.pyx"],
                             language="c++")]


    setup(name='tesserocr',
          version=find_version('tesserocr.pyx'),
          description='A simple, Pillow-friendly, Python wrapper around tesseract-ocr API using Cython',
          long_description=read('README.rst'),
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
              'Programming Language :: Python :: 3.2',
              'Programming Language :: Python :: 3.3',
              'Programming Language :: Python :: 3.4',
              'Programming Language :: Python :: 3.5',
              'Programming Language :: Python :: Implementation :: CPython',
              'Programming Language :: Python :: Implementation :: PyPy',
              'Programming Language :: Cython'
          ],
          keywords='Tesseract,tesseract-ocr,OCR,optical character recognition,PIL,Pillow,Cython',
          # cmdclass={'build_ext': CustomBuildExit},
          cmdclass={'build_ext': BuildTesseract},
          ext_modules=ext_modules,
          test_suite='tests'
          )
