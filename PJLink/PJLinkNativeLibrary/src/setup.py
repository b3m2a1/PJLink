# -*- coding: utf-8 -*-

from distutils.core import setup, Extension
import shutil, os, platform, sys
from PJLink.MathLinkEnvironment import MathLinkEnvironment as Env

setup_orig_dir = os.getcwd()
lib_dir = os.path.dirname(__file__)
build_dir = os.path.join(lib_dir, "build")
cur_dir = os.getcwd()
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
elif plat == "WINDOWS":
    # force gcc since I guess Windows default compiler dislikes some of my macros...?
    os.environ["CC"] = "g++"

if not os.path.exists(build_dir):
    os.mkdir(build_dir)

mathlink_lib_file = None
for lib in os.listdir(mathlink_dir):
    lname, ext = os.path.splitext(lib)
    if lname.endswith(mathlink_name) and (ext == ".a" or ext == ".lib"):
        mathlink_lib_file=os.path.join(build_dir, lib)
        shutil.copyfile(os.path.join(mathlink_dir, lib), mathlink_lib_file)

if not os.path.exists(mathlink_lib_file):
    raise IOError("MathLink library at {} doesn't exits".format(mathlink_lib_file))
print("Using MathLink library at {}".format(mathlink_lib_file))

if mathlink_lib_file is not None:
    if plat != "Linux":
        module1 = Extension(
            'PJLinkNativeLibrary',
            sources = ['PJLinkNativeLibrary.cpp'],
            library_dirs = [ build_dir ],
            libraries = [ mathlink_name ],
            include_dirs= [ mathlink_dir ]
        )
    else:
        module1 = Extension(
            'PJLinkNativeLibrary',
            sources = ['PJLinkNativeLibrary.cpp'],
            library_dirs = [ build_dir ],
            ##  ${LIBDIR}/libML64i4.a -lm -lpthr
            # ead -lrt -ldl -luuid
            libraries = [ mathlink_name, "m", "pthread", "rt", "dl", "uuid" ],
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
    # if not failed:
    #     shutil.rmtree(build_dir)

else:
    os.chdir(cur_dir)
    failed = True
    raise IOError("MathLink library version {} in directory {} not found".format(mathlink_name, mathlink_dir))