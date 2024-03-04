# https://docs.conda.io/projects/conda-build/en/stable/resources/package-spec.html

import os
import hashlib
import json
import tarfile
import tempfile
import zipfile
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from collections import namedtuple

WheelInfo = namedtuple("WheelInfo", ["package_name", "version", "python_version", "platform_tag"])


def sha256_checksum(filename):
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()


def parse_wheel_filename(wheel_path):
    wheel_name = os.path.basename(wheel_path)
    parts = wheel_name.rsplit('.whl', 1)[0].split('-')
    if len(parts) == 5:
        package_name, version, python_tag, abi_tag, platform_tag = parts
        python_version = python_tag[2:]  # e.g., cp310 -> 310
        return WheelInfo(package_name, version, python_version, platform_tag)
    else:
        raise ValueError("Unexpected wheel filename format")


def generate_index_json(wheel_info, tesseract_version):
    arch_map = {"win_amd64": ("x86_64", "win-64"), "win32": ("x86", "win-32")}
    arch, subdir = arch_map.get(wheel_info.platform_tag.split('.')[0], ("noarch", "noarch"))

    index_json = {
        "arch": arch,
        "build": f"py{wheel_info.python_version}_tesseract_{tesseract_version}_0",
        "build_number": 0,
        "depends": [
            f"python >= {wheel_info.python_version[:1]}.{wheel_info.python_version[1:]},<{wheel_info.python_version[:1]}.{int(wheel_info.python_version[1:]) + 1}.0a0"
        ],
        "license": "MIT",
        "name": wheel_info.package_name,
        "platform": "win",
        "subdir": subdir,
        "timestamp": int(datetime.now().timestamp() * 1000),
        "version": wheel_info.version,
    }
    return index_json


def extract_metadata_info(site_packages_path):
    # Locate the .dist-info directory
    dist_info_dirs = list(Path(site_packages_path).glob('*.dist-info'))
    if not dist_info_dirs:
        raise FileNotFoundError("No .dist-info directory found.")

    metadata_path = dist_info_dirs[0] / 'METADATA'

    # Initialize metadata dictionary
    metadata = {"home": "", "license": "", "summary": ""}

    # Extract the required information
    with open(metadata_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('Home-page:'):
                metadata['home'] = line.strip().split(': ', 1)[1]
            elif line.startswith('License:'):
                metadata['license'] = line.strip().split(': ', 1)[1]
            elif line.startswith('Summary:'):
                metadata['summary'] = line.strip().split(': ', 1)[1]

    return metadata


def convert_wheel_to_conda(wheel_path, tesseract_version, output_path):
    # Create a temporary directory for Conda package content
    with tempfile.TemporaryDirectory() as conda_dir:
        site_packages_path = os.path.join(conda_dir, 'Lib', 'site-packages')
        os.makedirs(site_packages_path, exist_ok=True)

        # Parse wheel info
        wheel_info = parse_wheel_filename(wheel_path)

        # Extract wheel
        with zipfile.ZipFile(wheel_path, 'r') as zip_ref:
            zip_ref.extractall(site_packages_path)

        # Extract metadata from METADATA file before deleting .dist-info directories
        metadata = extract_metadata_info(site_packages_path)

        # Delete *.dist-info directories at the first level of site_packages_path
        dist_info_dirs = Path(site_packages_path).glob('*.dist-info')
        for dist_info_dir in dist_info_dirs:
            if dist_info_dir.is_dir():  # Ensure it's a directory
                shutil.rmtree(dist_info_dir)

        # Create empty pyc file, so it will be tracked by "files" and later removed during uninstall
        pycache_dir = os.path.join(site_packages_path, wheel_info.package_name, "__pycache__")
        os.makedirs(pycache_dir, exist_ok=True)
        pyc_file = os.path.join(pycache_dir, f"__init__.cpython-{wheel_info.python_version}.pyc")
        open(pyc_file, 'a').close()

        # Process extracted files
        paths = []
        files_list = []
        for root, dirs, files in os.walk(site_packages_path):
            for file in files:
                file_path = Path(os.path.join(root, file))
                file_path_rel = file_path.relative_to(conda_dir)

                # Generate metadata for paths.json and files list
                paths.append({
                    "_path": file_path_rel.as_posix(),
                    "path_type": "hardlink",
                    "sha256": sha256_checksum(file_path),
                    "size_in_bytes": os.path.getsize(file_path)
                })
                files_list.append(file_path_rel.as_posix())

        info_dir = os.path.join(conda_dir, 'info')
        os.makedirs(info_dir, exist_ok=True)

        # Write paths.json (seems to be not strictly required?)
        # with open(os.path.join(info_dir, 'paths.json'), 'w') as f:
        #     json.dump({"paths": paths, "paths_version": 1}, f, indent=2)

        # Write the "files" file
        with open(os.path.join(info_dir, 'files'), 'w') as f:
            for file in files_list:
                f.write(file + '\n')

        # Write index.json
        with open(os.path.join(info_dir, 'index.json'), 'w') as f:
            json.dump(generate_index_json(wheel_info, tesseract_version), f, indent=2)

        # Generate and write the about.json file
        about_json_path = os.path.join(info_dir, 'about.json')
        with open(about_json_path, 'w') as f:
            json.dump(metadata, f, indent=4)

        # Ensure the output path exists
        os.makedirs(output_path, exist_ok=True)

        # Construct the final output file path
        archive_name = f"py{wheel_info.python_version}-{wheel_info.platform_tag}.tar.bz2"
        final_output_path = os.path.join(output_path, archive_name)

        # Archive as .tar.bz2 and save to the specified output path
        with tarfile.open(final_output_path, "w:bz2") as tar:
            for item_name in os.listdir(conda_dir):
                item_path = os.path.join(conda_dir, item_name)
                tar.add(item_path, arcname=item_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert a Python wheel to a Conda package.')
    parser.add_argument('wheel_path', type=str, help='Path to the wheel file to be converted.')
    parser.add_argument('tesseract_version', type=str, help='Version of the Tesseract to be included in the package.')
    parser.add_argument('output_path', type=str, help='Output path where the Conda package will be saved.')

    args = parser.parse_args()

    convert_wheel_to_conda(args.wheel_path, args.tesseract_version, args.output_path)
