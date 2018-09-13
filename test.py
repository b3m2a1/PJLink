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

import code; code.interact(local=locals())
