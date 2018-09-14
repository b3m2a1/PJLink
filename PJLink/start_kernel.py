"""start_kernel is a convenience script for starting a kernel thread in python

"""

import sys, os

true_file = os.path.abspath(__file__)

sys.path.insert(0, os.path.dirname(os.path.dirname(true_file)))

from PJLink import *

### I should do a lot more argparsing... but I don't

sys.argv.pop(0)
if len(sys.argv) > 0 and ( sys.argv[0] == "--blocking=true" or sys.argv[0] == "-b"):
    blocking = True
    sys.argv.pop(0)
else:
    blocking = False

if len(sys.argv) == 0:
    init = None
elif len(sys.argv) == 1:
    init = sys.argv[0]
else:
    init = sys.argv

reader = create_reader_link(init=init, debug_level=3)#, start = not blocking)
# print(reader.link.drain())

if blocking:
#     reader.run()
# else:
    import code
    code.interact(banner = "", local={"Kernel":reader.link, "KernelReader":reader})
