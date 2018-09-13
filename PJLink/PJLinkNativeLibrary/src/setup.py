# -*- coding: utf-8 -*-

from distutils.core import setup, Extension
import shutil, os, platform, sys
from PJLink.MathLinkEnvironment import MathLinkEnvironment as Env

setup_orig_dir = os.getcwd()
lib_dir = os.path.dirname(__file__)
os.chdir(lib_dir)

argv1 = sys.argv
argv2 = [ "build_ext", "--inplace" ]

mathlink_dir = os.path.join(Env.get_Mathematica_root(), "SystemFiles", "Links", "MathLink", "DeveloperKit")

plat = platform.system()
# if plat == "Darwin":
#
# elif plat == "Linux":
#     mathlink_dir = os.sep + os.path.join("Applications", mname, "Contents", "MacOS", "WolframKernel")
# elif plat == "Windows":
#     if mname is None:
#         mname = os.path.join("Mathematica", cls.CURRENT_MATHEMATICA)
#     elif isinstance(mname, float) or re.match(r"\d\d.\d", mname):
#         mname = os.path.join("Mathematica", str(mname))
#     bin = os.path.expandvars(os.path.join("%ProgramFiles%", "Wolfram Research", mname , "wolfram"))
# else:
#     raise ValueError("Don't know how to find the WolframKernel executable on system {}".format(plat))

module1 = Extension(
    'PJLinkNativeLibrary',
    sources = ['PJLinkNativeLibrary.cpp'],
    library_dirs = [ mathlink_dir ],
    libraries = [ "MLi4" ]
)

setup (name = 'PJLinkNativeLibrary',
       version = '1.0',
       description = 'Implementation of JLinkNativeLibrary for python',
       ext_modules = [module1]
       )

ext = ""
target = os.path.join(os.path.dirname(lib_dir), "PJLinkNativeLibrary")
src = None

for f in os.listdir(lib_dir):
    if f.endswith(".so"):
        ext = ".so"
        src = os.path.join(lib_dir, f)
        target += ext
    elif f.endswith(".pyd"):
        ext = ".pyd"
        src = os.path.join(lib_dir, f)
        target += ext

if src is not None:
    try:
        os.remove(target)
    except:
        pass
    os.rename(src, target)

failed = os.path.isfile(target)