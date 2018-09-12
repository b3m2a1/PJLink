"""PJLinkNativeLibrary attempts to import from the .so for now

Currently very much so not platform independent
"""

import os, sys

try:
    sys.path.insert(0, os.path.dirname(__file__))
    from PJLinkNativeLibrary import *
finally:
    sys.path.pop(0)

