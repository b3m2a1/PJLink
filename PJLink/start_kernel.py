"""start_kernel is a convenience script for starting a kernel thread in python

"""

import sys, os, argparse

sys.stdout.flush()

true_file = os.path.abspath(__file__)

sys.path.insert(0, os.path.dirname(os.path.dirname(true_file)))

from PJLink import *

parser = argparse.ArgumentParser(description='Start a PJLink kernel.')
parser.add_argument('--blocking', dest='block', type=bool, nargs='?', default=False,
                    help='whether the kernel should block or not')
parser.add_argument('--debug', dest='debug', type=int, nargs='?', default=0,
                    help='debug level for underlying PJLink lib')
parser.add_argument('--log', dest='log', type=str, nargs='?', default="",
                    help='log file for underlying PJLink lib')
parser.add_argument('--class', dest='cls', type=str, nargs='?', default="reader",
                    help='log file for underlying PJLink lib')
parser.add_argument('--mathematica', dest='vers', type=str, nargs='?', default = "",
                    help='path to Mathematica $InstallationDirectory')
parser.add_argument('-linkname', dest='name', type=str, nargs='?',
                    help='name for the link')
parser.add_argument('-linkmode', dest='mode', type=str, nargs='?',
                    help='mode for the link')
parser.add_argument('-linkprotocol', dest='protocol', type=str, nargs='?',
                    help='protocol for the link')

parser = parser.parse_args()

blocking = parser.block
debug = parser.debug
name = parser.name
mode = parser.mode
protocol = parser.protocol
cls = parser.cls
log = parser.log.strip("'").strip('"')
math= parser.vers.strip()

opts = { 'linkname' : parser.name, 'linkmode' : parser.mode, 'linkprotocol' : parser.protocol }
opts = [ ('-'+k, v) for k, v in opts.items() if v is not None]
init = [ None ] * (2 * len(opts))
for i, t in enumerate(opts):
    init[2*i] = t[0]
    init[2*i+1] = t[1]

if len(math)>0:
    import re
    if re.match(r'\d+.\d.+', math):
        Env.CURRENT_MATHEMATICA = math
    else:
        Env.INSTALLATION_DIRECTORY = math

if cls == "reader":
    reader = create_reader_link(init=init, debug_level=debug, log = log)
    local = {"Kernel":reader.link, "KernelReader":reader}
elif cls == "kernel":
    kernel = create_kernel_link(init=init, debug_level=debug, log = log)
    local = {"Kernel":kernel}
elif cls == "native":
    link = create_math_link(init=init, debug_level=debug, log = log)
    local = {"Link":link}
else:
    raise ValueError("Can't parse link class {}".format(cls))

if blocking:
    import code
    code.interact(banner = "", local= local)
