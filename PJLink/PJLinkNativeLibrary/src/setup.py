# -*- coding: utf-8 -*-

from distutils.core import setup, Extension
import shutil, os, platform, sys
from PJLink.MathLinkEnvironment import MathLinkEnvironment as Env

setup_orig_dir = os.getcwd()
lib_dir = os.path.dirname(__file__)
os.chdir(lib_dir)

### HACKS! ;___;
plat = Env.PLATFORM
mathlink_dir = Env.get_MathLink_library()
mathlink_name = Env.get_MathLink_library_name()
if plat == "Darwin":
    # print(os.environ["MACOSX_DEPLOYMENT_TARGET"])
    try:
        cur_targ = os.environ["MACOSX_DEPLOYMENT_TARGET"]
    except KeyError:
        cur_targ = None
    if cur_targ is None or float(cur_targ[:4])<10.9:
        os.environ["MACOSX_DEPLOYMENT_TARGET"]="10.9" #minimum target with cstdint

module1 = Extension(
    'PJLinkNativeLibrary',
    sources = ['PJLinkNativeLibrary.cpp'],
    library_dirs = [ mathlink_dir ],
    libraries = [ mathlink_name ],
    include_dirs= [ mathlink_dir ]
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

failed = not os.path.isfile(target)