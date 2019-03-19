import sys, platform, os, shutil
from .load_lib import _get_lib_dir_loc, libdata

try:
    loc = _get_lib_dir_loc()
    sys.path.insert(0, loc)
    if not libdata._NATIVE_LIBRARY_EXISTS:
        raise ImportError("No PJLinkNativeLibrary to load")
    # if platform.platform() == "Windows":
    #     so = libdata._NATIVE_LIBRARY_SHARED_OBJECT
    #     base, ext = os.path.splitext(so)
    #     shutil.copy(so, base+"_d"+ext)
    for file in os.listdir(loc):
        print(file)
    from PJLinkNativeLibrary import *
finally:
    sys.path.pop(0)