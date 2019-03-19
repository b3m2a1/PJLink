import sys
from .load_lib import _get_lib_dir_loc

try:
    sys.path.insert(0, _get_lib_dir_loc())
    from PJLinkNativeLibrary import *
finally:
    sys.path.pop(0)