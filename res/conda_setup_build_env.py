import re
import os
import argparse


# usage:
# > python conda_setup_build.py <wheel_path> <tesseract_version> <output_folder>


# Instantiate the parser
parser = argparse.ArgumentParser()
parser.add_argument('wheel_path', type=str)
parser.add_argument('tesseract_version', type=str)
parser.add_argument('output_folder', type=str)
args = parser.parse_args()

# meta.yaml and bld.bat are required for "conda build"
meta_yaml = """package:
  name: tesserocr
  version: {tesserocr_version}
build:
  number: {build_number}
  string: py{python_version}_tesseract_{tesseract_version}_{build_number}
requirements:
  build:
    - python
  run:
    - python
about:
    home: https://github.com/sirfz/tesserocr
    license: MIT
    summary: A simple, Pillow-friendly, Python wrapper around tesseract-ocr API using Cython"""

bld_bat = """pip install \"{wheel_path}\""""


def create_meta_yaml(python_version, tesserocr_version, tesseract_version, build_number, output_folder):
    file_content = meta_yaml.format(
        python_version=python_version,
        tesserocr_version=tesserocr_version,
        tesseract_version=tesseract_version,
        build_number=build_number
    )

    with open(os.path.join(output_folder, "meta.yaml"), "w") as f:
        f.write(file_content)


def create_bld_bat(wheel_path, output_folder):
    file_content = bld_bat.format(wheel_path=wheel_path)

    with open(os.path.join(output_folder, "bld.bat"), "w") as f:
        f.write(file_content)


# parse tesserocr and python version from wheel file
regex = r"tesserocr-(\d+\.\d+\.\d+)-cp(\d+)-cp.*\.whl"
filename = os.path.basename(args.wheel_path)
result = re.findall(regex, filename)[0]
tesserocr_version = result[0]
python_version = result[1]

create_meta_yaml(python_version, tesserocr_version, args.tesseract_version, 0, args.output_folder)
create_bld_bat(args.wheel_path, args.output_folder)
