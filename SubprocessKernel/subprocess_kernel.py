"""subprocess_kernel.py is a little script for starting a subprocess kernel in python

"""

from SubprocessKernel import SubprocessKernel
import argparse

### I should do a lot more argparsing... but I don't

parser = argparse.ArgumentParser(description='Start a PJLink kernel.')
parser.add_argument('--blocking', dest='block', type=bool, nargs='?', default=False,
                    help='whether the kernel should block or not')
parser.add_argument('--debug', dest='debug', type=int, nargs='?', default=0,
                    help='debug level for underlying PJLink lib')
parser.add_argument('--init', dest='init', type=str, nargs='?',
                    help='custom init string for the link')
parser.add_argument('-linkname', dest='name', type=str, nargs='?',
                    default="", help='name for the link')
parser.add_argument('-linkmode', dest='mode', type=str, nargs='?',
                    help='mode for the link')
parser.add_argument('-linkprotocol', dest='protocol', type=str, nargs='?',
                    help='protocol for the link')

parser = parser.parse_args()

init_string = parser.init
blocking = parser.block
debug = parser.debug
name = parser.name
mode = parser.mode
protocol = parser.protocol

if len(init_string) > 0:
    init = init_string
    if init == "None":
        init = None
else:
    opts = { 'linkname' : parser.name, 'linkmode' : parser.mode, 'linkprotocol' : parser.protocol }
    opts = [ ('-'+k, v) for k, v in opts.items() if v is not None]
    init = [ None ] * (2 * len(opts))
    for i, t in enumerate(opts):
        init[  2*i  ] = t[0]
        init[ 2*i+1 ] = t[1]

link = SubprocessKernel(init, debug_level=debug)

M = link.M

Kernel = link
Mathematica = M
Evaluate = link.evaluate

link.start()

if blocking:
    import code
    code.interact(banner = "",  local = {"Kernel" : Kernel, "Mathematica" : Mathematica, "Evaluate" : Evaluate})