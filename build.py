from .PJLink.PJLinkNativeLibrary import setup
import sys

sys.exit(1 if setup.failed else 0)