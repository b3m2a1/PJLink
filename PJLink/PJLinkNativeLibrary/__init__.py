from .load_lib import _get_lib_dir_loc
import sys

try:
    sys.path.insert(0, _get_lib_dir_loc())
    from PJLinkNativeLibrary import *
finally:
    sys.path.pop(0)

