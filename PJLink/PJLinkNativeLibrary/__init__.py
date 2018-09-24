"""PJLinkNativeLibrary attempts to import from the .so for now

Currently very much so not platform independent
"""

import os, sys, platform

_NATIVE_LIBRARY_EXISTS = False
def _get_lib_dir_loc():
    global _NATIVE_LIBRARY_EXISTS
    targ_dir_base = os.path.dirname(__file__)
    plat = platform.system()
    if plat == "Darwin":
        sys_name = "MacOSX"
    else:
        sys_name = plat

    ext_list = [ "-"+platform.machine().replace("_", "-"), "" ]
    for ext in ext_list:
        targ_dir = os.path.join(targ_dir_base, sys_name + ext)
        bin_test_so = os.path.join(targ_dir, "PJLinkNativeLibrary.so")
        bin_test_pyd = os.path.join(targ_dir, "PJLinkNativeLibrary.pyd")
        if os.path.isfile(bin_test_so) or os.path.isfile(bin_test_pyd):
            _NATIVE_LIBRARY_EXISTS = True
            break
    else:
        targ_dir = targ_dir_base
        for f in os.listdir(targ_dir_base):
            if f.endswith(".so") or f.endswith(".pyd"):
                _NATIVE_LIBRARY_EXISTS = True
                break
        else:
            sys.path.insert(0, os.path.join(targ_dir_base, "src"))
            argv1 = sys.argv
            sys.argv = [ "build", "build_ext", "--inplace" ]
            try:
                import setup as setup
            finally:
                sys.path.pop(0)
                sys.argv = argv1

            if setup.failed:
                _NATIVE_LIBRARY_EXISTS = False
                raise ImportError("No library file found")
            else:
                _NATIVE_LIBRARY_EXISTS = True

    return targ_dir

try:
    sys.path.insert(0, _get_lib_dir_loc())
    from PJLinkNativeLibrary import *
finally:
    sys.path.pop(0)

