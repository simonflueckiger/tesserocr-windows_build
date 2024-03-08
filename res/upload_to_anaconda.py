import os
import re
import functools
import subprocess
import argparse


# usage:
# > python upload_to_anaconda.py <conda_packages_path>
#
# where <conda_packages_path> points to to a folder with the following layout
#
# ├───<conda_packages_path>
# │   ├───win-32
# │   │       <wheel_files>
# │   │
# │   └───win-64
# │           <wheel_files>


# Instantiate the parser
parser = argparse.ArgumentParser()
parser.add_argument('conda_packages_path', type=str)
args = parser.parse_args()

subfolders = ["win-32", "win-64"]


def wheel_file_cmp(item1, item2):
    # tesserocr-2.5.2-py36_tesseract_4.1.1_0.tar.bz2
    # is smaller than
    # tesserocr-2.5.2-py310_tesseract_4.1.1_0.tar.bz2

    regex = R"py(\d+)\D"
    ver1 = re.findall(regex, item1)[0]
    ver2 = re.findall(regex, item2)[0]

    major1 = int(ver1[0])
    major2 = int(ver2[0])

    minor1 = int(ver1[1:])
    minor2 = int(ver2[1:])

    if major1 > major2:
        return 1
    elif major1 < major2:
        return -1
    else:
        if minor1 > minor2:
            return 1
        elif minor1 < minor2:
            return -1
        else:
            return 0


for subfolder in subfolders:
    folder = os.path.join(args.conda_packages_path, subfolder)
    wheels = os.listdir(folder)
    wheels = sorted(wheels, key=functools.cmp_to_key(wheel_file_cmp))

    for wheel in wheels:
        wheel_path = os.path.join(args.conda_packages_path, subfolder, wheel)
        subprocess.run(["anaconda", "upload", wheel_path, "-i"])
