"""NativeLink implements the MathLink interface via native methods in JLinkNativeLibrary. These
native methods in turn call the MathLink C library. NativeLink is the only point where J/Link "touches"
the native library. NativeLink inherits a lot from MathLinkImpl, which handles generic logic that does
not require direct calls into the native library. The code that resides in NativeLink is just the lowest
layer of the functionality of a MathLink implementation, where there is nothing left to do but call into
the MathLink C library."""

from .MathLink import MathLink
from .MathLinkExceptions import *
from .HelperClasses import *

###############################################################################################
#                                                                                             #
#                                           LinkBase                                          #
#                                                                                             #
###############################################################################################

class NativeLink(MathLink):

    # This is intended to be used within J/Link to determine whether the native
    # library is loaded and therefore whether it is OK to do things that would require it to be loaded.
    # Right now, only the Expr class uses this, to decide whether it can use a loopback link. It does not want
    # to attempt to load the library if it has not been loaded already.
    __NATIVE_LIBRARY_LOADED = False
    __lib = None
    __LIBRARY_LOAD_EXCEPTION = None
    __NATIVE_LIBRARY_EXISTS = False

    def __init__(self, init = None, debug_level = 0):

        self.__USE_NUMPY = None

        import os, re

        if init is None:
            bin = self.Env.get_Mathematica_binary()
            init = ["-linkmode", "launch", "-linkname", "'{}' -mathlink -wstp".format(bin)]#, "-mathlink", "-wstp"]
        elif isinstance(init, str) and os.path.isfile(init):
            init = ["-linkmode", "launch", "-linkname", "'\"{}\" -mathlink -wstp'".format(init)]#, "-mathlink", "-wstp"]
        elif isinstance(init, float) or re.match(r"\d\d.\d", init):
            bin = self.Env.get_Mathematica_binary(init)
            init = ["-linkmode", "launch", "-linkname", "'\"{}\" -mathlink -wstp'".format(bin)]#, "-mathlink", "-wstp"]


        import threading
        self.__lock = threading.RLock()
        self._init = init
        self.__errMsgOut = [ "" ]
        self._loadNativeLibrary(debug_level=debug_level)

        import time
        with self.__lock:
            if isinstance(init, str):
                # MLForceYield forces yielding under Unix even in the presence of a yield function.
                link, cap = self.__lib.OpenString(
                    self,
                    init + " -linkoptions MLForceYield",
                    self.__errMsgOut
                )
                self.__link = link
                self._MLINK = cap
                time.sleep(.5)
            elif isinstance(init, tuple) and isinstance(init[0], int):
                cap, link = init
                self.__link = link
                self._MLINK = cap._MLINK
            else:
                init.extend(("-linkoptions", "MLForceYield"))
                cap, link = self.__lib.Open(
                    self,
                    len(init),
                    init,
                    self.__errMsgOut
                )
                self.__link = link
                self._MLINK = cap
                time.sleep(.5)

        if self.__link == 0:
            if len(self.__errMsgOut) > 0:
                err_msg = self.__errMsgOut[0]
            else:
                err_msg = None
            raise MathLinkException("CreationFailed")

    @property
    def native_library_loaded(self):
        return self.__NATIVE_LIBRARY_LOADED
    @property
    def library_load_exception(self):
        return self.__LIBRARY_LOAD_EXCEPTION

    def _loadNativeLibrary(self, *args, initialize = True, debug_level = None, setup = True):
        import os
        ## args is just a sneaky hack to force using keywords
        if not self.__NATIVE_LIBRARY_LOADED:
            if setup:
                targ_dir = os.path.join(os.path.dirname(__file__), "PJLinkNativeLibrary")
                for f in os.listdir(targ_dir):
                    if f.endswith(".so") or f.endswith(".pyd"):
                        self.__NATIVE_LIBRARY_EXISTS = True
                        break
                else:
                    import PJLink.PJLinkNativeLibrary.src.setup as setup
                    if setup.failed:
                        raise ImportError("No library file found")

            try:
                import PJLink.PJLinkNativeLibrary as pj
            except ImportError as e:
                self.__LIBRARY_LOAD_EXCEPTION = e
                raise e
            else:
                self.__NATIVE_LIBRARY_LOADED = True
                self.__lib = pj
                if isinstance(debug_level, int):
                    pj.setDebugLevel(None, debug_level)
                if initialize:
                    pj.Initialize()

    def __sig_handler(self, sig, frame):
        # these don't actually seem to do what I wanted...

        import signal
        sig_names = {
            signal.SIGSEGV : "InvalidMemoryAccess",
            signal.SIGABRT : "Abort",
            signal.SIGINT  : "Interrupt",
            signal.SIGTERM : "Terminate"
        }
        try:
            sig_name = sig_names[sig]
        except KeyError:
            sig_name = sig
        raise MathLinkException("SignalCaught", "Signal {}".format(sig_name))

    def _lib_call(self, meth, *args):
        import signal
        self._loadNativeLibrary()

        handled_sigs = [ signal.SIGABRT, signal.SIGSEGV, signal.SIGTERM, signal.SIGINT]
        og_handlers = [ signal.getsignal(sig) for sig in handled_sigs ]
        for sig in handled_sigs:
            signal.signal(sig, self.__sig_handler)

        try:
            lib_meth = getattr(self.__lib, meth)
            res = lib_meth(*args)
        except Exception as e:
            argstr = "Exception in MathLink call '{}': ".format(meth) + e.args[0]
            e.args = (argstr, )
            raise e
        finally:
            for sig, handle in zip(handled_sigs, og_handlers):
                signal.signal(sig, handle)

        return res

    def _lib_func(self, meth):
        self._loadNativeLibrary()
        res = getattr(self.__lib, meth)
        return res

    def _call(self, meth, *args):
        return self._lib_call(meth, self, *args)

    @property
    def link(self):
        return self.__link

    @property
    def thread_lock(self):
        return self.__lock

    def _wrap(self, checkLink = True, checkError = True, check = None, lock = True):
        return LinkWrapper(self, checkLink, checkError, check, lock)

    def close(self):
        if self.__link != 0:
            with self.__lock:
                self.__lib.Close(self)
            self.__link = 0

    @staticmethod
    def _isException(errCode, check=None):
        if check is None:
            err = errCode != 0 and errCode != 10
        elif isinstance(check, int):
            err = errCode != check
        elif isinstance(check, str):
            err = errCode != Env.getErrorInt(check)
        elif callable(check):
            err = check(errCode)
        else:
            try:
                err = errCode not in check
            except:
                raise ValueError("cannot test error code against check {}".format(check))
        return err

    def _check_link(self):
        if self.__link == 0:
            raise MathLinkException("LinkIsNull")

    def _check_error(self, allowed = None):
        errCode = self._call("Error")
        if self._isException(errCode, allowed):
            raise MathLinkException(errCode, self._call("ErrorMessage"))

    def _connect(self):
        with self._wrap():
            return self._call("Connect")

    def _name(self):
        with self._wrap():
            return self._call("Name")

    def _newPacket(self):
        return self._call("NewPacket")

    def _nextPacket(self):
        with self._wrap():
            return self._call("NextPacket")

    def _endPacket(self):
        with self._wrap():
            return self._call("EndPacket")

    def _error(self):
        if self.__link == 0:
            return self.Env.getErrorInt("LinkIsNull")
        else:
            return self._call("Error")

    def _clearError(self):
        if self.__link == 0:
            return False
        else:
            return self._call("ClearError")

    def _errorMessage(self):
        if self.__link == 0:
            return MathLinkException.lookupMessageText("LinkIsNull")
        else:
            err = self._error()
            if err >= self.Env.getErrorInt("NonMLError"):
                msg = MathLinkException.lookupMessageText(err)
            else:
                msg = self._call("ErrorMessage")
            return msg

    def _setError(self, err):
        return self._call("SetError", err)

    def _ready(self):
        with self._wrap(checkError=False):
            return self._call("Ready")

    def flush(self):
        with self._wrap():
            return self._call("Flush")

    def _getNext(self):
        with self._wrap(check=0):
            return self._call("GetNext")

    def _getType(self):
        with self._wrap(check=0):
            t = self._call("GetType")
            return t

    def _putNext(self, ptype):
        with self._wrap():
            return self._call("PutNext", ptype)

    def _getArgCount(self):
        with self._wrap():
            return self._call("GetArgCount")

    def _putArgCount(self, argc):
        with self._wrap():
            return self._call("PutArgCount", argc)

    def _putSize(self, size):
        with self._wrap():
            return self._call("PutSize", size)

    def _bytesToPut(self):
        with self._wrap():
            return self._call("BytesToPut")

    def _bytesToGet(self):
        with self._wrap():
            return self._call("BytesToGet")

    def _putData(self, data, num=None):
        from array import array
        with self._wrap():
            if isinstance(data, (bytes, bytearray)):
                pass
            elif isinstance(data, array) and data.typecode == 'b':
                pass
            else:
                raise ValueError("cannot interpret data as bytes-compatible object")
            if not isinstance(num, int):
                num = len(data)
            return self._call("PutData", data, num )
    def _getData(self, num):
        with self._wrap():
            return self._call("GetData", num)
    def _getString(self):
        with self._wrap(check=0):
            str = self._call("GetString") # for reasons unknown this adds a character...
            # if len(str) > 0:
            #     str = str[1:]
            return str
    def _getByteString(self, missing):
        with self._wrap(check=0):
            return self._call("GetByteString", missing)
    def _putByteString(self, data, num=None):
        from array import array
        with self._wrap():
            if isinstance(data, (bytes, bytearray)):
                pass
            elif isinstance(data, array) and data.typecode == 'b':
                pass
            else:
                raise ValueError("cannot interpret data as bytes-compatible object")
            if not isinstance(num, int):
                num = len(data)
            return self._call("PutByteString", data, num)
    def _getSymbol(self):
        with self._wrap(check=0):
            str = self._call("GetSymbol") # for reasons unknown this adds a character...
            # print(str)
            # str = str.replace("\x00", "") # for unknown reasons this adds null bytes
            return str
    def _putSymbol(self, s):
        with self._wrap():
            # print("asdasdasd", s)
            return self._call("PutSymbol", s)
    def _putString(self, s):
        with self._wrap():
            # print(s)
            self._call("PutString", s)
    def _putBool(self, b):
        with self._wrap():
            return self._call("PutSymbol", "True" if b else "False")

    def _putInt(self, i):
        with self._wrap():
            return self._call("PutInteger", i)
    def _putDouble(self, f):
        with self._wrap():
            return self._call("PutDouble", f)

    def _getByte(self):
        return self._getInt()
    def _getShort(self):
        return self._getInt()
    def _getLong(self):
        return self._getInt()
    def _getInt(self):
        with self._wrap(check=0):
            return self._call("GetInteger")
    def _getBool(self):
        with self._wrap(check=0):
            return self._call("GetSymbol") == "True"
    def _getFloat(self):
        with self._wrap(check=0):
            return self._call("Get")
    def _getDouble(self):
        with self._wrap(check=0):
            return self._call("GetDouble")
    def _getChar(self):
        return chr(self._getInt())

    def _putReal0(self, d, callstr):
        import math
        with self._wrap():
            if d is math.inf:
                self._call("PutSymbol", "Infinity")
            elif d is -math.inf:
                self._putFunction("DirectedInfinty", 1)
                self._putInt(-1)
            elif d is math.nan:
                self._call("PutSymbol", "Indeterminate")
            else:
                self._call(callstr, d)

    def _putFloat(self, d):
        self._putReal0(d, "PutDouble")
    def _putTrueFloat(self, d):
        self._putReal0(d, "PutFloat")

    def _getFunction(self):
        with self._wrap(check=0):
            t = self.Env.fromTypeToken(self._call("GetType"))
            if t == 'Error':
                self._check_error()
            elif t != 'Function':
                # print(self._getSingleObject(t))
                self._setError(3)
                self._check_error()
            argc = self._getArgCount()
            head = self._getSymbol()
            return MLFunction(head, argc)

    def _putFunction(self, f, argCount = None):
        if isinstance(f, MLFunction):
            f, argCount = f.name, f.argCount
        elif argCount is None:
            raise ValueError("Can't put function without argcount")
        with self._wrap():
            self._call("PutNext", self.Env.toTypeToken('Function'))
            self._call("PutArgCount", argCount)
            self._call("PutSymbol", f)

    def _checkFunction(self, f, argCount = None):

        if isinstance(f, MLFunction):
            f, argCount= f.name, f.argCount

        if argCount is None:
            with self._wrap(check=0):
                return self._call("CheckFunction", f)
        else:
            with self._wrap():
                return self._call("CheckFunctionWithArgCount", f, argCount)

    def transferExpression(self, source):
        with self._wrap():
            with source._wrap():
                if isinstance(source, NativeLink):
                    self._call("TransferExpression", source.link)
                elif hasattr(source, "getMathLink"):
                    self.transferExpression(source.getMathLink())
                else:
                    self.put(source.getExpr())

    def transferToEndOfLoopbackLink(self, source):
        with self._wrap():
            with source._wrap():
                if hasattr(source, "getLink"):
                    self._call("TransferToEndOfLoopbackLink", source.getLink())
                else:
                    while source.ready():
                        self.transferExpression(source)

    def _getMessage(self):
        with self._wrap(checkError=False, lock=False):
            return self._call("GetMessage")

    def _putMessage(self, msg):
        with self._wrap(checkError=False, lock=False):
            msg_cached = msg
            if not isinstance(msg, int):
                msg = self.Env.getMessageInt(msg)
            if msg is None:
                raise ValueError("MathLink error message {} unknown".format(msg_cached))
            return self._call("PutMessage", msg)

    def _messageReady(self):
        with self._wrap(checkError=False, lock=False):
            return self._call("MessageReady")

    def _createMark(self):
        with self._wrap(checkError=False, lock=False):
            mark = self._call("CreateMark")
            if mark == 0:
                raise MathLinkException("Memory", "Not enough memory to create Mark")
            else:
                return mark

    def _seekMark(self, mark):
        with self._wrap(checkError=False, checkLink=False):
            if self.__link != 0:
                self._call("SeekMark", mark)

    def _destroyMark(self, mark):
        with self._wrap(checkError=False, checkLink=False):
            if self.__link != 0:
                self._call("DestroyMark", mark)

    def _setYieldFunctionOn(self, target, meth):
        # Convenient to set a yielder while a thread is blocking in MathLink. Thus, this method is not synchronized.
        # Instead, we synch on an object that is specific to the yielder-handling data structures.
        # synchronized (yieldFunctionLock) {
        # This next line sets up the call from yielderCallback() to user's method.
        with self.__yieldFunctionLock:
            res = super()._setYieldFunctionOn(target, meth)
            destroyYielder = (meth == None or not res)
            # This sets up or destroys the callback from C to the nativeYielderCallback method.
            self._call("SetYieldFunction", destroyYielder)
            return res

    def _addMessageHandlerOn(self, target, meth):
        result = super()._addMessageHandlerOn(target, meth)
        if result:
            # This establishes a callback from C to the nativeMessageCallback method.
            self._call("SetMessageHandler")
        return result

    def _getArray(self, otype, depth, head_List=None):

        import array

        tname = self.Env.getTypeNameFromTypeInt(otype)

        tc = self.Env.getTypeCodeFromTypeInt(tname)
        if isinstance(tc, str) and tc in array.typecodes and ( depth == 1 or not self.Env.allowRagged()):
            with self._wrap(check=0):
                res_array = self._call("GetArray", otype, depth, head_List)
                err_code = self._error()
                MathLinkException.raise_non_ml_error(err_code)
        else:
            # print(otype)
            res_array = super()._getArray(otype, depth, head_List)

        return res_array

    def _putArray(self, o, headList=None):
        # Already guaranteed by caller (MathLinkImpl) that data is an array and not null. All
        # by-value array-putting work goes through this function.
        with self._wrap():
            # MathLink C API array functions have trouble with 0-length arrays. It is easiest to catch these up in Java
            # and force them to be routed through MLPutArray(), which has special code to handle this case. In other words,
            # we must make sure that arrays with a 0 anywhere in their dimensions get sent the slow way: putArraySlices().

            arr, tint, dims, depth = self._get_put_array_params(o) # will not be accurate for ragged arrays, but we won't use the result in that case.
            # print(arr, tint, dims, depth)

            if tint is not None:
                sent = False
                if depth == 1:
                    if isinstance(arr, BufferedNDArray):
                        arr = arr._buffer
                    self._call("PutArray", tint, arr, None if headList is None else headList[0])
                    sent = True
                elif depth > 1 and tint not in map(self.Env.toTypeInt, ("String", "Boolean")):
                    # Much faster to create a new flattened (1-D) array, to match the C-style memory layout of arrays.
                    # This can be sent very efficiently over the link down in the native library. The cost is memory--an
                    # extra copy of the array data is made here. To turn off this behavior and fall back to the slow method
                    # (which was always used prior to J/Link 1.1), use a Java command line with -DJLINK_FAST_ARRAYS=false.

                    # We're going to assume the arr implements the buffer interface and that furthermore it's got
                    # a single contiguous memory block.
                    # That should be sufficient here to make everything work nicely

                    if isinstance(arr, BufferedNDArray):
                        arr = arr._buffer
                    # print(arr, tint, dims)
                    self._call("PutArrayFlat", tint, arr, headList, dims)
                    sent = True

                if not sent:
                    # Either ragged, or other tests above were not met. Must send as slices.
                    # This is equivalent to the pre-J/Link 1.1 method, except that the array is unwound in Java, not C.
                    # We only call native code to put the last level of the array (a 1-dimensional slice). This method
                    # works for everything, and it allows ragged arrays. It can be very slow for arrays where the product
                    # of the first depth - 1 dimensions is very large (say, > 50000). In other words, slowness is probably
                    # only an issue for very large depth >= 3 arrays.
                    # putArraySlices needs full explicit heads array, not null.
                    explicit_heads = [ "List" ] * depth
                    if headList is not None:
                        for i, el in enumerate(headList):
                            explicit_heads[i] = str(el)

                    self._putArraySlices(arr, tint, explicit_heads, 0)

            else:
                self._putArrayPiecemeal(o, headList, 0)

    def _putArraySlices(self, o, tint, head_list, head_index ):
        if head_index == len(head_list) - 1:
            self._call("PutArray", tint, o, head_list[head_index])
        else:
            self._putFunction(head_list[head_index], len(o))
            for e in o:
                self._putArraySlices(e, tint, head_list, head_index + 1)

    def nativeYielderCallback(self, ignore):
        return self._yielderCallback()

    def nativeMessageCallback(self, message, n):
        return self._messageCallback(message, n)

    @property
    def use_numpy(self):
        if self.__USE_NUMPY is None:
            self.__USE_NUMPY = self.Env.HAS_NUMPY
            self._setUseNumPy(self.Env.HAS_NUMPY)

        return self.__USE_NUMPY

    @use_numpy.setter
    def use_numpy(self, val):
        self._setUseNumPy(bool(val))

    def _setUseNumPy(self, flag):
        """Sets NumPy usage at the C level"""

        flag = bool(flag)
        self.__USE_NUMPY = flag
        self._call("setUseNumPy", flag)

    def _getUseNumPy(self):
        """Gets whether or not NumPy usage has been set at the C level and sets that for the object"""
        res = self._call("getUseNumPy")
        self.__USE_NUMPY = res
        return res

    def _setDebugLevel(self, val):
        """Sets the debug level for the link"""
        self._call("setDebugLevel", val)