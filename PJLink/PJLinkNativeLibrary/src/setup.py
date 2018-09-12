# -*- coding: utf-8 -*-

from distutils.core import setup, Extension
import shutil, os

try:
    shutil.rmtree(os.path.join(os.getcwd(), "build"))
except:
    pass

module1 = Extension(
    'PJLinkNativeLibrary',
    sources = ['PJLinkNativeLibrary.cpp'],
    library_dirs = [ os.path.join(os.getcwd(), "SystemResources") ],
    libraries = [ "MLi4" ]
    )

setup (name = 'PJLinkNativeLibrary',
       version = '1.0',
       description = 'Implementation of JLinkNativeLibrary for python',
       ext_modules = [module1]
       )

target = "~/Documents/Python/IDEA/PJLink/PJLink/PJLinkNativeLibrary/PJLinkNativeLibrary.so"
src = "~/Documents/C++/PJLinkNativeLibrary/build/lib.macosx-10.9-x86_64-3.7/PJLinkNativeLibrary.cpython-37m-darwin.so"
try:
    os.remove(os.path.expanduser(target))
except:
    pass
os.rename(os.path.expanduser(src), os.path.expanduser(target))

print("done")
