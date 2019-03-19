"""PJLinkNativeLibrary attempts to import from the .so or .pyd for now

"""

import os, sys, platform

class libdata:
    _NATIVE_LIBRARY_EXISTS = False
    _NATIVE_LIBRARY_SHARED_OBJECT = None
    _NATIVE_LIBRARY_BASE_DIR = os.path.dirname(__file__)

def _find_native_library_dir(libdata=libdata):

    targ_dir_base = libdata._NATIVE_LIBRARY_BASE_DIR
    plat = platform.system()
    if plat == "Darwin":
        sys_name = "MacOSX"
    else:
        sys_name = plat

    mach = platform.machine().replace("AMD", "x86-").replace("_", "-")
    ext_list = [ "-"+mach, "" ]
    for ext in ext_list:
        targ_dir = os.path.join(targ_dir_base, sys_name + ext)
        bin_test_so = os.path.join(targ_dir, "PJLinkNativeLibrary.so")
        bin_test_pyd = os.path.join(targ_dir, "PJLinkNativeLibrary.pyd")
        if os.path.isfile(bin_test_so):
            libdata._NATIVE_LIBRARY_SHARED_OBJECT = bin_test_so
        elif os.path.isfile(bin_test_pyd):
            libdata._NATIVE_LIBRARY_SHARED_OBJECT = bin_test_pyd
        if libdata._NATIVE_LIBRARY_SHARED_OBJECT is not None:
            libdata._NATIVE_LIBRARY_EXISTS = True
            break
    else:
        targ_dir = targ_dir_base
        for f in os.listdir(targ_dir_base):
            if f.endswith(".so") or f.endswith(".pyd"):
                libdata._NATIVE_LIBRARY_SHARED_OBJECT = os.path.join(targ_dir_base, f)
                libdata._NATIVE_LIBRARY_EXISTS = True
                break

    return targ_dir

def _get_lib_dir_loc(libdata=libdata):
    targ_dir = _find_native_library_dir()
    if not libdata._NATIVE_LIBRARY_EXISTS:
        targ_dir_base = libdata._NATIVE_LIBRARY_BASE_DIR
        sys.path.insert(0, os.path.join(targ_dir_base, "src"))
        argv1 = sys.argv
        sys.argv = [ "build", "build_ext", "--inplace" ]
        try:
            import setup as setup
        finally:
            sys.path.pop(0)
            sys.argv = argv1

        if setup.failed:
            libdata._NATIVE_LIBRARY_EXISTS = False
            raise ImportError("No library file found")
        else:
            libdata._NATIVE_LIBRARY_EXISTS = True
            targ_dir = _find_native_library_dir()

    return targ_dir