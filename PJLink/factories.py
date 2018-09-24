"""This provides all the factory methods that don't need encapsulation in a class

"""

from .KernelLink import WrappedKernelLink
from .NativeLink import NativeLink
from .Reader import Reader
from .MathLinkEnvironment import MathLinkEnvironment as Env

def create_math_link(init = None, debug_level = 0, log = ""):
    if isinstance(log, str):
        import os
        if len(log)>0 and os.path.exists(os.path.dirname(log)):
            Env.LOG_FILE = log
            Env.ALLOW_LOGGING = True
    link = NativeLink(init, debug_level)
    return link

def create_kernel_link(init = None, debug_level = 0, log = ""):
    # should do more but I'm tired
    link =create_math_link(init = init, debug_level= debug_level, log = log)
    kernel = WrappedKernelLink(link)
    return kernel

def create_reader_link(init = None, debug_level = 0, log = "", start = True):
    kernel = create_kernel_link(init = init, debug_level = debug_level, log = log)
    reader = Reader.create_reader(kernel, start = start)
    return reader