"""start_kernel is a convenience script for starting a kernel thread in python

"""

import sys, os, argparse

sys.stdout.flush()

true_file = os.path.abspath(__file__)

sys.path.insert(0, os.path.dirname(os.path.dirname(true_file)))

from PJLink import *

### I should do a lot more argparsing... but I don't

parser = argparse.ArgumentParser(description='Start a PJLink kernel.')
parser.add_argument('--blocking', dest='block', type=bool, nargs='?', default=False,
                    help='whether the kernel should block or not')
parser.add_argument('--debug', dest='debug', type=int, nargs='?', default=0,
                    help='debug level for underlying PJLink lib')
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

opts = { 'linkname' : parser.name, 'linkmode' : parser.mode, 'linkprotocol' : parser.protocol }
opts = [ ('-'+k, v) for k, v in opts.items() if v is not None]
init = [ None ] * (2 * len(opts))
for i, t in enumerate(opts):
    init[2*i] = t[0]
    init[2*i+1] = t[1]

reader = create_reader_link(init=init, debug_level=debug)
# print(reader.link.drain())

# stdout = open(os.path.expanduser("~/Desktop/stdout.txt"), "w+")
# stderr = open(os.path.expanduser("~/Desktop/stderr.txt"), "w+")
# sys.stdout = stdout
# sys.stderr = stderr

if blocking:
#     reader.run()
# else:
    import code
    code.interact(banner = "", local={"Kernel":reader.link, "KernelReader":reader})
