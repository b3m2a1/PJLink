from PJLink import *
from PJLink.KernelLink import *

#########################################################################################################

# from PJLink.HelperClasses import *
#
# # dims = [5, 3, 2, 5]
# # size = 1
# # for d in dims:
# #     size *= d
# # barr = BufferedNDArray.from_iterable(range(size), dims)
#
# M = MPackage

#########################################################################################################

# link = create_math_link(debug_level=3)
# link.connect()
# print("Error:", link._error())
# print("SetError:", link._setError(2))
# print("Error:", link._error())
# print("ClearError:", link._clearError())
# print("Error:", link._error())
# print("NewPacket:", link._newPacket())
# print("PutFunction:", link._putFunction("EvaluatePacket", 1))
# print("Put:", link.put("Hello from python"))
# print("Flush:", link.flush())
# print("Ready:", link.ready)
# print("GetNext:", link._getNext())
# print("ErrorMessage:", link._errorMessage())
# print("GetNext:", link._getNext())
# print("GetType:", link.close())

#########################################################################################################

# link = WrappedKernelLink()

# link = create_kernel_link(None, debug_level=0)
# print("Name:", link.name)
# print("Connected:", link.connect())
# print(link._getFunction(), link.drain())
# print(link.evaluateToInputForm("$Version"))
# # link.use_numpy = False
# print(link.evaluate(link.M.F("Transpose", [[1, 2, 3], [1, 2, 3]])))
# link._raiseLastError()

#########################################################################################################

# reader = create_reader_link()
# link = reader.link
# link.drain()
# def test_call():
#     return link.evaluate(link.M.ToExpression("LinkWrite[Links[][[1]], CallPacket[1, 1]]"))
# def test_eval(evstr):
#     return link.evaluate(link.M.ToExpression('LinkWrite[Links[][[1]], CallPacket[1, "Evaluate"@"{}"]]'.format(evstr)))
# # print(test_call())

#
#
# link = WrappedKernelLink()
#
# with LinkEnvironment(link):
#     asd = 2

# banda = BufferedNDArray.from_iterable(range(27), [3, 3, 3])
# print(banda.data)

from PJLink import *
create_kernel_link()

#########################################################################################################

# from PJLink.MathLinkEnvironment import MathLinkEnvironment as Env
#
# print(Env.get_Installed_Mathematica())
# print(Env.get_Mathematica_name())
# print(Env.get_Mathematica_root())
# print(Env.get_MathLink_library())

#########################################################################################################
















#########################################################################################################


import code
code.interact(banner = "", local=locals())
