# Python 3.7 Built-in packages
from distutils.core import setup, Extension
from shutil import copy, rmtree
from pathlib import Path
import sys
import argparse
from src.misc import is_mac, is_linux, is_windows


def compile(args):
    include_dir = Path(args.python_h).as_posix()
    c_source = args.s
    print(f"Directory chosen for Python.h : {include_dir}")
    # Name the package accordingly to the OS
    file_name = 'tanimoto_processing'
    if is_windows():
        file_name = "clib_w64." + file_name
    elif is_linux():
        file_name = "clib_linux64." + file_name
    elif is_mac():
        file_name = "clib_mac64." + file_name
    module1 = Extension(
        'src.'+file_name
        , sources=[c_source]
        , include_dirs=[include_dir]
    )

    setup(
        name='tanimoto_processing'
        , version='1.2'
        , description='Fingerprint processing package.'
        , ext_modules=[module1]
        , author="Valentin Guillaume, Ludovic Chaput"
        , packages=["src"]
    )
    build_dir = Path(Path(sys.argv[0]).parent, "build")
    if build_dir.is_dir():
        rmtree(build_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script used to compile the C library into a callable python module.")
    parser.add_argument("python_h", help="Python.h header file location")
    parser.add_argument("-s", help="Source file location", default="src/tanimoto_processing.c")
    # parser.add_argument("--build-lib", help="Do not ", default=".", dest="d")

    args, unknown = parser.parse_known_args()

    # Changing the sysargv for distutil.core.setup
    sys.argv = [*sys.argv[:1], "build", "--build-lib", '.']

    compile(args)
