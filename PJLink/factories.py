"""This provides all the factory methods that don't need encapsulation in a class

"""

from .KernelLink import WrappedKernelLink
from .NativeLink import NativeLink
from .Reader import Reader

def create_math_link(init = None, debug_level = 0):
    # should do more but I'm tired
    link = NativeLink(init, debug_level)
    return link

def create_kernel_link(init = None, debug_level = 0):
    # should do more but I'm tired
    link = NativeLink(init, debug_level)
    kernel = WrappedKernelLink(link)
    return kernel

def create_reader_link(init = None, debug_level = 0, start = True):
    kernel = create_kernel_link(init, debug_level)
    reader = Reader.create_reader(kernel, start = start)
    return reader