import sys
from .load_lib import _get_lib_dir_loc, libdata

try:
    loc = _get_lib_dir_loc()
    sys.path.insert(0, loc)
    if not libdata._NATIVE_LIBRARY_EXISTS:
        raise ImportError("No PJLinkNativeLibrary to load")
    from PJLinkNativeLibrary import *
finally:
    sys.path.pop(0)