from PJLink import *

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

link = create_kernel_link(None, debug_level=0)
print("Name:", link.name)
print("Connected:", link.connect())
print(link._getFunction(), link.drain())
print(link.evaluateToInputForm("$Version"))
print(link.evaluate(link.M.F("Transpose", [[1, 2, 3], [1, 2, 3]])))
link._raiseLastError()

#########################################################################################################
#########################################################################################################
#########################################################################################################

# from PJLink import NativeLink
# nl = NativeLink.NativeLink(["-linkmode", "launch", "-linkname", "/Applications/Mathematica.app/Contents/MacOS/WolframKernel"])

# from array import typecodes
# print(array.typecodes)

# from PJLink.HelperClasses import BufferedNDArray
# import array
#
# ba = BufferedNDArray(array.array('i', [1, 2, 3, 4, 5, 6, 7, 8, 9]), [3, 3])
# print(ba)
# print(ba[0], ba[1], ba[2])
#
# ba.extend(array.array('i', [1, 2, 3, 4]))
# ba.adjust()
# ba.slide(3)
#
# print(ba[0], ba[1], ba[2])

# import timeit
#
# print(timeit.timeit( "ArrayUtils.nones((5, 5, 5))" , "from PJLink.HelperClasses import ArrayUtils", number=10))
# print(timeit.timeit( "np.nones((5, 5, 5))",  "import numpy as np", number=10))

# class blah:
#     def __init__(self, asd):
#         self.__farts = asd
#
#     @classmethod
#     def make_shit(cls, bleb):
#         boob = cls(None)
#         boob.__farts = bleb
#         return boob
#
#     @property
#     def farts(self):
#         return self.__farts
#
#
# print(blah("a").__name__)



# from PJLink.HelperClasses import BufferedNDArray
# from array import array
# ar = array('l', range(5*5*5*5))
# da = BufferedNDArray(ar, [5, 5, 5, 5])
# da[1:2] = [range(125)]
# da[0:2, 1, 1:2, 1] = [[10], [20]]
# print(da[0:2, 1, 1:2, 1].tonumpy())


# def funct(a, b, c, *args, f=1, d=2, e=3, **kwargs):
#     pass
#
# def funct2(a, b, c, f=1, d=2, e=3):
#     pass
#
# def funct3(*args):
#     print(args)
#
# import types
# def change_func_args(function, *new_args, **new_kwargs):
#     """ Create a new function with its arguments renamed to new_args. """
#     code_obj = function.__code__
#     # the arguments are just the first co_argcount co_varnames
#     # replace them with the new argument names in new_args
#     # also gotta take in the ff.co_kwonlyargcount I guess...
#     acount = len(new_args) + len(new_kwargs)
#     acount_2 = code_obj.co_argcount + code_obj.co_kwonlyargcount
#     new_kwarg_keys = list(new_kwargs.keys())
#     new_varnames = tuple(list(new_args) + list(new_kwarg_keys) +
#                          list(code_obj.co_varnames[acount_2:]))
#     # type help(types.CodeType) at the interpreter prompt for information
#     new_code_obj = types.CodeType(
#         len(new_args),
#         len(new_kwargs),
#         code_obj.co_nlocals,
#         code_obj.co_stacksize,
#         code_obj.co_flags,
#         code_obj.co_code,
#         code_obj.co_consts,
#         code_obj.co_names,
#         new_varnames,
#         code_obj.co_filename,
#         code_obj.co_name,
#         code_obj.co_firstlineno,
#         code_obj.co_lnotab,
#         code_obj.co_freevars,
#         code_obj.co_cellvars
#     )
#     modified = types.FunctionType(new_code_obj, function.__globals__)
#     function.__defaults__ = tuple(new_kwargs.values())
#     function.__code__ = modified.__code__  # replace code portion of original
#
# change_func_args(funct3, "a", "b", "c")

#from PJLink.HelperClasses import MExprUtils as M
#
# M.register_function("CreateDocument", "data", "___", WindowMargins=None)
#
#print(M.Names("Pr*", _EndPacket=True))
#
# floop = {}
# floop.update(a=1, c=2)
# print(floop)
# import inspect
#
# print(inspect.signature(M.EvaluatePacket))

#########################################################################################################
#########################################################################################################
#########################################################################################################


import code; code.interact(local=locals())
