from .MathLink import MathLink
from .MathLinkExceptions import MathLinkException
from .HelperClasses import *

###############################################################################################
#                                                                                             #
#                                         KernelLink                                          #
#                                                                                             #
###############################################################################################

class KernelLink(MathLink):
    """KernelLink is the largest and most important class in J/Link. It implements the entire
KernelLink interface, including all internal support methods and fields, except (more or less)
the MathLink interface (it does inherit significant implementation of MathLink via MathLinkImpl).
KernelLink is implemented here in terms of the MathLink interface. To create an implementation
of KernelLink, you can just subclass KernelLinkImpl and provide implementations of the low-level
MathLink interface methods. All the complex logic that makes a KernelLink beyond a MathLink is coded
here. Put another way, KernelLinkImpl is the repository for a huge amount of reusable logic that
creates the extra functionality of KernelLink via calls to methods in the lower MathLink interface.

The main class that extends this one is WrappedKernelLink, which implements the raw MathLink
put/get methods by forwarding them to the MathLink implementation it "wraps". Other KernelLink
implementation classes that extend this one will want to override more of its KernelLink
implementation if they are not happy with its fine-grained use of the MathLink methods
(e.g., the experimental KernelLink_HTTP overrides most of the methods to make them single network hits).

Readers who want to understand how the "installable Java" features of J/Link (i.e., calling Java
from Mathematica), will want to start with the handleCallPacket() method here.
"""

    __LAST_EXCEPTION = None
    __LAST_EXCEPTION_DURING_CALL_HANDLING = None
    __LAST_MESSAGE = None
    __FEServerLink = None

    def __init__(self):
        self.M = MPackage
        self.ObjectHandler = ObjectHandler
        super().__init__()
        self._EXEC_ENV = { "Kernel":self , "Mathematica": self.M, "Evaluate": self.evaluateString }

    def get(self):
        # Replace TYPE_FLOATORINT and TYPE_DOUBLEORINT (and arrays of them) with just TYPE_FLOAT and TYPE_DOUBLE.
        # Those "ORINT" constants are just for pattern matching in Mathematica. They could be stripped out of the RHS of
        # the jCallJava definitions in Mathematica, but it is more efficient and convenient to just do it here, as the args
        # are being read.

        res = None
        tk = self._getType()
        t1 = self.Env.fromTypeToken(tk)

        with LinkMark(self) as mark:

            self.Env.logf("Getting {} off link", t1)

            if t1 == "Function":
                try:
                    self.Env.log("Checking if object is packed array")
                    self._checkFunction(self.M.PackagePackage+"PackedArrayInfo") # this can get messy with context?
                    self.Env.log("Found packed array on link")

                    dtype = self._getSymbol()
                    self.Env.logf("Got array type {}", dtype)

                    true_type = None
                    if isinstance(dtype, MLSym):
                        dtype = dtype.name
                    if dtype == "Integer":
                        true_type = self.Env.toTypeInt("Integer")
                    elif dtype == "Real":
                        true_type = self.Env.toTypeInt("Double")
                    elif dtype == "Complex":
                        true_type = self.Env.toTypeInt("Complex")

                    self.Env.log("Getting array dimensions")
                    dims = list(self._getArray(self.Env.toTypeInt("Integer"), 1))
                    self.Env.logf("Got array dimensions {}", dims)

                    tok = self.Env.fromTypeToken(self._getNext())
                    self.Env.logf("Got next token {}", tok)

                    if tok in ("Object", "Symbol"):
                        res = self._getObject()
                    else:
                        # print("Unpacking packed array of type {} and dims {}".format(dtype, dims))
                        # unpacking = True
                        res = self._getArray(true_type, len(dims))
                except MathLinkException as e:
                    # import traceback as tb

                    # self.Env.log(tb.format_exc())
                    self._clearError()
                    self._seekMark(mark)
                    # if unpacking:
                    #     raise e
                    # print(e)

            if res is None:

                if t1 == "Object":
                    res = self._getObject()
                elif t1 == "Function":
                    res = self.getPacket()
                else:
                    try:
                        res = self._getSingleObject(t1)
                        # print(res)
                    except (MathLinkException, ValueError, TypeError) as e:
                        import traceback as tb

                        self._clearError()
                        self.Env.log(tb.format_exc())
                        pass # Maybe I should handle these?
                    else:
                        if t1 == "Symbol":
                            res = MLSym(res)

        self.Env.logf("Got {} off link", res)

        return res

    def getPacket(self):
        tok = self._getTypeName()
        if tok == "Function":
            f = self._getFunction()
            # print(f)
            args = [ self.get() for i in range(f.argCount) ]
            pkt = self.M.F(f.head, *args)
        else:
            pkt = None
        return pkt

    def evaluate(self, expr, wait = True):
        self._evaluateExpr(self.M._add_type_hints(expr))
        if wait:
            self.waitForAnswer()
            return self.get()

    def evaluateString(self, expr, wait=True):
        self._evaluateString(self.M._add_type_hints(expr))
        if wait:
            self.waitForAnswer()
            return self.get()

    def _evaluateExpr(self, s):
        self.put(self.M._eval(s))
        self.flush()
    def _evaluateString(self, s, **opts):
        self._evaluateExpr(self.M.ToExpression(s, **opts))
    def _evaluateExportString(self, o, fmt, **kw):
        self._evaluateExpr(self.M.ExportString(o, fmt, **kw))

    def evaluateToOutputForm(self, e, page_width=0):
        return self._eval_to_string(e, page_width, "OutputForm")
    def evaluateToInputForm(self, e, page_width=0):
        return self._eval_to_string(e, page_width, "InputForm")
    def evaluateToTypeset(self, e, page_width=0, use_std_form=True):
        return self._eval_to_typeset(e, page_width, use_std_form)
    def evaluateToImage(self, e, export_format = None, **kwargs):
        ### Include an option to use PIL here
        return self._eval_to_image(e, export_format = export_format, **kwargs)
    def evaluateToJSON(self, o):
        return self._eval_to_format(o, "JSON")
    def evaluateToMathML(self, e):
        return self._eval_to_string(e, 0, "MathMLForm")

    def waitForAnswer(self):
        self.__accumulatingPS = [] # some old-ass setting for working with PostScript I assume
        while True:
            pkt = self._nextPacket()
            allowDefaultProcessing = self.notifyPacketListeners(pkt)
            if allowDefaultProcessing:
                self._handlePacket(pkt)
            if self.Env.getPacketName(pkt) in ("Return", "InputName", "ReturnText", "ReturnExpr"):
                break
            else:
                self._newPacket()

        return pkt

    def discardAnswer(self):
        pkt = self.waitForAnswer()
        self._newPacket()
        pkt_name = self.Env.getPacketName(pkt)
        while pkt_name not in ("Return", "InputName"):
            # This loop will only happen once, of course, but might as well be defensive.
            pkt = self.waitForAnswer()
            pkt_name = self.Env.getPacketName(pkt)
            self._newPacket()

    def _putPacket(self, pkt, arg_count = 1):
        if isinstance(pkt, int):
            pkt = self.Env.getPacketName(pkt)
        self._putFunction(pkt, arg_count)

    def _handlePacket(self, pkt):
        pkt_name = self.Env.getPacketName(pkt)
        self.Env.logf("Handling packet {}", pkt_name)
        if pkt_name in ("Return", "InputName", "ReturnText", "ReturnExpr", "Menu", "Message"):
            # maybe debug print them?
            pass
        elif pkt_name == "Call":
            otype = self._getType()
            tname = self.Env.fromTypeToken(otype)
            self.Env.logf("Handling call packet of type {}", tname)
            if tname == "Integer":
                # A normal CallPacket representing a call to Java via jCallJava.
                self.__handleCallPacket()
            elif self.FEServerLink is not None:
                # A CallPacket destined for the FE via MathLink`CallFrontEnd[] and routed through
                # Java due to ShareFrontEnd[]. This would only be in a 5.1 or later FE, as earlier
                # versions do not use CallPacket and later versions would use the FE's Service Link.
                feLink = self.FEServerLink
                feLink.putFunction("CallPacket", 1)
                feLink.transferExpression(self)
                # FE will always reply to a CallPacket. Note that it is technically possible for
                # the FE to send back an EvaluatePacket, which means that we really need to run a
                # little loop here, not just write the result back to the kernel. But this branch
                # is only for a 5.1 and later FE, and I don't think that they ever do that.
                self.transferExpression(feLink);
        elif pkt_name == "Input" or pkt_name == "InputString":
            if self.FEServerLink is not None:
                fe = self.FEServerLink
                fe._putPacket(pkt_name)
                fe.put(self._getString())
                fe.flush()
                self._newPacket()
                self.put(fe._getString())
                self.flush()
        elif pkt_name == "Display" or pkt_name == "DisplayEnd":
            if self.FEServerLink is not None:
                fe = self.FEServerLink
                try:
                    ps = self.__accumulatingPS
                except AttributeError:
                    self.__accumulatingPS = None
                if self.__accumulatingPS is None:
                    self.__accumulatingPS = []
                self.__accumulatingPS.append(self._getString())
                if pkt_name == "DisplayEnd":
                    fe = self.FEServerLink
                    # XXXPacket[stuff] ---> Cell[GraphicsData["PostScript", stuff], "Graphics"]
                    fe._putFunction("FrontEnd`FrontEndExecute", 1)
                    fe._putFunction("FrontEnd`NotebookWrite", 2)
                    fe._putFunction("FrontEnd`SelectedNotebook", 0)
                    fe._putFunction("Cell", 2)
                    fe._putFunction("GraphicsData", 2)
                    fe.put("PostScript")
                    fe.put("".join(self.__accumulatingPS))
                    fe.put("Graphics")
                    fe.flush()
                    self.__accumulatingPS = None
        elif pkt_name == "Text" or pkt_name == "Expression":
            fe = self.FEServerLink
            if fe is not None:
                fe._putFunction("FrontEnd`FrontEndExecute", 1)
                fe._putFunction("FrontEnd`NotebookWrite", 2)
                fe._putFunction("FrontEnd`SelectedNotebook", 0)
                fe._putFunction("Cell", 2)
                fe.transferExpression(self)
                fe.put("Message" if self.__last_packet_was_message else "Print")
                fe.flush()
            elif pkt_name == "Expression":
                self._getFunction()

        elif pkt_name == "FE":
            # This case is different from the others. At the point of entry, the link is at the point
            # _before_ the "packet" has been read. As a result, we must at least open the packet.
            # Note that FEPKT is really just a fall-through for unrecognized packets. We don't have any
            # checks that it is truly intended for the FE.
            fe = self.FEServerLink
            if fe is not None:
                mark = self._createMark()
                try:
                    wrapper = self._getFunction()
                    if not wrapper.name == "FrontEnd`FrontEndExecute":
                        fe._putFunction("FrontEnd`FrontEndExecute", 1)
                finally:
                    self._seekMark(mark)
                    self._destroyMark(mark)

                fe.transferExpression(self)
                fe.flush()
                # Wait until either the fe is ready (because what we just sent causes a return value)
                # or kernel is ready (the computation is continuing because the kernel is not waiting
                # for a return value).
                import time
                while not fe.ready() or not self.ready():
                    time.sleep(.06)

                if fe.ready():
                    self.transferExpression(fe)
                    self.flush()
        else:
            # It's OK to get here. For example, this happens if you don't share the fe, but have a
            # button that calls NotebookCreate[]. This isn't a very good example, because that
            # function expects the fe to return something, so Java will hang. you will get into
            # trouble if you make calls on the fe that expect a return. Everything is OK for calls
            # that don't expect a return, though.
            self._getFunction()

        self.__last_packet_was_message = pkt_name == "Message"

    def _getLastError(self):
        err_no = self._error()
        if self.Env.getErrorName(err_no) != "Ok":
            self.__LAST_EXCEPTION = MathLinkException(self._error(), self._errorMessage)
        return self.__LAST_EXCEPTION
    @property
    def last_error(self):
        if self.__LAST_EXCEPTION is None:
            self._getLastError()

        return self.__LAST_EXCEPTION
    def _raiseLastError(self):
        err = self.last_error
        if isinstance(err, Exception):
            raise err


    def interruptEvaluation(self):
        try:
            self._putMessage("Interrupt")
        except MathLinkException:
            pass
    def abortEvaluation(self):
        try:
            self._putMessage("Abort")
        except MathLinkException:
            pass
    def terminateKernel(self):
        try:
            self._putMessage("Terminate")
        except MathLinkException:
            pass
    def abandonEvaluation(self):
        self.setYieldFunction(self._bailoutYielder)
    def _bailoutYielder(self):
        self.setYieldFunction(None)
        return True

    def print(self, s):
        try:
            self.put(self.M._eval(
                self.M.F("Print", s)
            ))
            self.discardAnswer()
        except MathLinkException:
            self._clearError()
            self._newPacket()

    def message(self, symtag, args ):
        if not isinstance(args, (list, tuple)):
            args = [ args ]
        try:
            self.put(
                self.M._eval(
                    self.M.F("Apply",
                        self.M.ToExpression("Function[Null, Message[#1, ##2], HoldFirst]"),
                        self.M.F("Join",
                            self.M.F("ToHeldExpression", symtag),
                            self.M.F("Hold", args)
                        )
                    )
                )
            )
            self.discardAnswer()
        except MathLinkException:
            self._clearError()
            self._newPacket()

    def wasInterrupted(self):
        msg_name = self.Env.getMessageInt(self.__LAST_MESSAGE)
        return msg_name in ("Interrupt", "Abort")

    def clearInterrupt(self):
        self.__LAST_MESSAGE = None

    def _messageHandler(self, msg, ignore):
        self.__LAST_MESSAGE = msg

    def _getObjectTypePair(self):

        res = None

        t = t_orig = self._getInt()

        t_flint = self.Env.toTypeInt("FloatOrInt")
        t_dubint = self.Env.toTypeInt("DoubleOrInt")
        t_float = self.Env.toTypeInt("Float")
        t_dub = self.Env.toTypeInt("Double")
        arr_int = self.Env.toTypeInt("Array1D")

        # print(t, arr_int, t % arr_int, t_flint, t_dubint, abs(t) // abs(arr_int) )

        if t % arr_int == t_flint:
            # TYPE_FLOAT + TYPE_ARRAY1 * (type / TYPE_ARRAY1);
            t = t_float + arr_int * ( -1 if t / abs(t) == 1 else 1) *( abs(t) // abs(arr_int) )
        elif t % arr_int == t_dubint:
            # TYPE_DOUBLE + TYPE_ARRAY1 * (type / TYPE_ARRAY1)
            t = t_dub + arr_int * ( -1 if t / abs(t) == 1 else 1) *( abs(t) // abs(arr_int) )

        if t == t_dubint:
            t = t_dub
        elif t == t_flint:
            t = t_float

        # print(t_orig, t)

        name = self.Env.fromTypeInt(t, "typename")
        # print(name)

        if name in (  "Integer", "Long", "Short", "Byte", "Char", "Float", "Double", "Boolean" ):
            res = self._getSingleObject(t)
        elif name == "String":
            tok = self._getTypeName()
            if tok == "Object":
                res = self._getObject()
            else:
                res = self._getString()
                if tok == "Symbol" and res == "Null":
                    return MLSym("Null")

        elif name == "Complex":
            with LinkMark(self) as mark:
                tok = self.Env.fromTypeToken(self._getNext())
                if tok == "Object":
                    res = self._getObject()
                elif tok == "Symbol":
                    res = self._getSymbol()
                    if res == "Null":
                        res = MLSym("Null") # can't remember how _getSymbol() is working
                    elif res != MLSym("Null"):
                        self._seekMark(mark)
                        res = self._getComplex()
                else:
                    self._seekMark(mark)
                    res = self._getComplex()

        elif name == "BigInteger":
            with LinkMark(self) as mark:
                tok = self.Env.fromTypeToken(self._getNext())
                if tok == "Object":
                    res = self._getObject()
                elif tok == "Symbol":
                    res = self._getSymbol()
                    if res == "Null":
                        res = MLSym("Null") # can't remember how _getSymbol() is working
                    elif res != MLSym("Null"):
                        self._seekMark(mark)
                        res = self._getInt()
                else:
                    self._seekMark(mark)
                    res = self._getInt()

        elif name == "Decimal":
            with LinkMark(self) as mark:
                tok = self.Env.fromTypeToken(self._getNext())
                if tok == "Object":
                    res = self._getObject()
                elif tok == "Symbol":
                    res = self._getSymbol()
                    if res == "Null":
                        res = MLSym("Null") # can't remember how _getSymbol() is working
                    elif res != MLSym("Null"):
                        self._seekMark(mark)
                        res = self._getDecimal()
                else:
                    self._seekMark(mark)
                    res = self._getDecimal()

        elif name == "Expr":
            with LinkMark(self) as mark:
                tok = self.Env.fromTypeToken(self._getNext())
                if tok == "Object":
                    res = self._getObject()
                elif tok == "Symbol":
                    res = self._getSymbol()
                    if res == "Null":
                        res = MLSym("Null") # can't remember how _getSymbol() is working
                    elif res != MLSym("Null"):
                        self._seekMark(mark)
                        res = self._getExpr()
                else:
                    self._seekMark(mark)
                    res = self._getExpr()

        elif name == "Bad":
            return res

        else:

            tchar = self._getNext() # dunno if this will break things?
            tname = self.Env.fromTypeToken(tchar)
            if tname == "Object" or tname == "Symbol":
                res = self._getObject()
            elif tname == "Function":
                res = self.getPacket()

            if res is None:
                for r in range(2, 1+self.Env.MAX_ARRAY_DEPTH):
                    tar = self.Env.toTypeInt("Array{}D".format(r))
                    if t > tar:
                        res = self._getArray(t - tar, r - 1)

        return res

    def _getArray(self, otype, depth, headList=None):
        # Although this method is intended for object arrays, detect cases where user specifies a
        # primitive type and make these go via the older getArray() API, which is optimized for
        # primitive arrays.

        if not isinstance(otype, int):
            otype = self.Env.toTypeInt(otype)

        # tname = self.Env.fromTypeInt(otype, "typename")
        return self._getArray0(otype, depth, headList, None)

    def _getArray0(self, otype, depth, headList = None, array_type = None):
        # Worker function for getting arrays of objects. All non-object cases are forwarded to superclass.
        # This function cannot do automatic flattening of arrays that are deeper than the requested depth,
        # which is done for other array types.

        res_arr = None

        tname = self.Env.fromTypeInt(otype)
        if tname == "Object":
            try:
                # Figure out the depth of the array and its leaf class type. Note that the detected leaf class type
                # is only used of the elementType argument is null.
                mark = self._createMark()
                mf = self._getFunction()
                actualDepth = 1
                if mf.argCount == 0:
                    # User is passing {} to specify a 0-length array of objects. We don't have type information
                    # here, so we don't know what type the array should be. Returning null would not be very useful,
                    # so we reutrn a 0-length array of Object.
                    firstInstance = self._getObject()
                else:
                    while actualDepth < self.Env.MAX_ARRAY_DEPTH:
                        tok = self._getNext()
                        name = self.Env.fromTypeToken(tok)
                        if name == "Function":
                            self._getFunction()
                            actualDepth+=1
                        else:
                            break
                    firstInstance = self._getObject()
            finally:
                self._seekMark(mark)
                self._destroyMark(mark)


            #Ignore the class of the first instance if user supplied a non-null elementClass argument.
            leafClass = array_type if isinstance(array_type, type) else type(firstInstance)
            if actualDepth < depth:
                raise MathLinkException("ArrayTooShallow")
            # Up through here, we have done what is necessary to flatten an array that is deeper than
            # requested. We have determined the actual depth of the array, and not just used the
            # requested depth. From here on, though, we assume the array is no deeper than requested.

            if depth == 1:
                func = self._getFunction()
                res_arr = [ leafClass(self._getObject()) for i in range(func.argCount) ]
                if headList != None:
                    headList[0] = func.name
            else:
                # We need to call getArraySlices ourselves, rather than just letting it happen from super.getArray(),
                # because we need to supply the array element class manually.
                res_arr = self._getArraySlices(otype, depth, headList, 0, leafClass)
        else:
            super()._getArray(otype, depth, headList)

    def _getObject(self):
        obj = None
        try:
            obj = self.ObjectHandler.get_object(self._getSymbol(), self._EXEC_ENV)
        except (MathLinkException, NameError): # might be more if the symbol is malformatted...
            # Convert exceptions thrown by getSymbol() (wasn't a symbol at all) or ObjectHandler.getObject()
            # (symbol wasn't a valid object ref) into MLE_BAD_OBJECT exceptions.
            raise MathLinkException("BadObject")
        return obj

    def _nextIsObject(self):
        # Tests whether symbol waiting on link is a valid object reference. Returns false for the symbol Null.
        # Called by getNext() and getType(), after it has already been verified that the type is MLTKSYM.

        mark = None
        res = False
        try:
            mark = self._createMark()
            # Note that this behavior means that the symbol Null on the link will result in MLTKSYM, not MLTKOBJECT.
            # This is desired (?) for backward compatibility.
            res = self._getObject() is not None
        except MathLinkException as e:
            self._clearError()
        finally:
            if mark is not None:
                self._seekMark(mark)
                self._destroyMark(mark)
        return res

    def __handleCleanException(self, exc):
        # "Clean" means that we have not tried to put any partial result on the link yet. This is not
        # a user-visible function. It is only called while handling calls from Mathematica (i.e.,
        # handleCallPacket() is on the stack).

        # Currently we do not check wasInterrupted() here and send back Abort[], on the grounds
        # that the exeption message is probably more useful than $Aborted. But it might be better
        # to send back Abort[] and thus stop the entire computation.

        self.__LAST_EXCEPTION_DURING_CALL_HANDLING = exc
        try:
            self._clearError()
            self._newPacket()
            if self.wasInterrupted():
                self._putFunction("Abort", 0)
            else:
                import traceback as tb
                self.put(self.M.F(self.M.PackageContext+"PythonTraceback", tb.format_exc()))
            self._endPacket()
            self.flush()
        except MathLinkException as e:
            # Need to send something back on link, or this will not be an acceptable branch.
            # About the only thing to do is call endPacket and hope that this will cause
            # $Aborted to be returned.
            try:
                import traceback as tb
                self.put(self.M.F(self.M.PackageContext+"PythonTraceback", tb.format_exc()))
                self._endPacket()
            except MathLinkException:
                self.put(b'$Failed')
                self._endPacket()

    def __handleCallPacket(self):
        """

        :return:
        """

        ind = 0
        try:
            ind = self._getInt()
        except MathLinkException as e:
            self.__handleCleanException(e)
            return

        if ind != self.Env.getCallInt("GetException"):
            self.__LAST_EXCEPTION_DURING_CALL_HANDLING = None

        try:
            name = self.Env.getCallName(ind)
            self.Env.logf("Enter call packet {}", name)
            if name == "CallPython":
                self.__callPython()
            elif name == "Throw":
                raise NotImplemented
            elif name == "ReleaseObject":
                raise NotImplemented
            elif name == "Val":
                raise NotImplemented
            elif name == "OnLoadCLass":
                raise NotImplemented
            elif name == "OnUnloadClass":
                raise NotImplemented
            elif name == "SetComplex":
                raise NotImplemented
            elif name == "Reflect":
                raise NotImplemented
            elif name == "Show":
                raise NotImplemented
            elif name == "SameQ":
                raise NotImplemented
            elif name == "InstanceOf":
                raise NotImplemented
            elif name == "AllowRagged":
                raise NotImplemented
            elif name == "GetException":
                raise NotImplemented
            elif name == "ConnectToFE":
                self.__connectToFEServer()
            elif name == "DisconnectToFE":
                self.__disconnectToFEServer()
            elif name == "PeekClasses":
                raise NotImplemented
            elif name == "PeekObjects":
                raise NotImplemented
            elif name == "SetUserDir":
                raise NotImplemented
            elif name == "ClassPath":
                raise NotImplemented
            elif name == "AddToClassPath":
                raise NotImplemented
            elif name == "UIThreadWaiting":
                raise NotImplemented
            elif name == "AllowUIComputations": # allowUIComputations
                raise NotImplemented
            elif name == "YieldTime": # yieldTime
                raise NotImplemented
            elif name == "GetConsole": # getConsole
                raise NotImplemented
            elif name == "ExtraLinks": # extraLinks
                raise NotImplemented
            elif name == "GetWindowID": # getWindowID
                raise NotImplemented
            elif name == "AddTitleChangeListener": #addTitleChangeListener
                raise NotImplemented
            elif name == "SetVMName": #setVMName()
                raise NotImplemented
            elif name == "SetException": #setException()
                raise NotImplemented
        except Exception as e:
            self.__handleCleanException(e)
            self.__LAST_EXCEPTION_DURING_CALL_HANDLING = e
            # self.put(tb.format_exc())
            # self.Env.log(tb.format_exc())
        finally:
            # self.Env.log("end handle call packet")
            self._clearError()
            try:
                self._newPacket()
                self._endPacket()
                self.flush()
            except MathLinkException as e:
                self.__handleCleanException(e)

    def _eval_to_string(self, obj, page_width = None, format = None):

        res = None
        try:
            self.__LAST_EXCEPTION = None
            self.put(self.M._eval_to_string_packet(obj, page_width, format))
            self.flush()
            self.waitForAnswer()
            res = self._getString()
            # print(res)
        except MathLinkException as e:
            self._clearError()
            self.__LAST_EXCEPTION = e
        finally:
            self._newPacket()

        return res

    def _eval_to_typeset(self, obj, page_width = None, use_standard_form=True):

        image_data = None
        try:
            self.__LAST_EXCEPTION = None
            self.put(self.M._eval_to_string_packet(obj, page_width, format))
            self.flush()
            self.waitForAnswer()
        except MathLinkException as e:
            self._clearError()
            self.__LAST_EXCEPTION = e
            self._newPacket()
            return image_data

        try:
            ntype = self._getNext()
            tname = self.Env.fromTypeToken(ntype)  # this pattern should maybe be a function...
            if tname == "String":
                image_data = self._getByteString(0)
        except Exception as e:
            self._clearError()
            self.__LAST_EXCEPTION = e

        return image_data

    def _eval_to_image(self, obj, export_format = None, **kw):
        # definitely find a way to use PIL...

        image_data = None
        try:
            self.__LAST_EXCEPTION = None
            self.put(self.M._eval_to_image_packet(obj, export_format = export_format, **kw))
            self.flush()
            self.waitForAnswer()
        except MathLinkException as e:
            self._clearError()
            self.__LAST_EXCEPTION = e
            self._newPacket()
            return image_data

        try:
            ntype = self._getNext()
            tname = self.Env.fromTypeToken(ntype)  # this pattern should maybe be a function...
            if tname == "String":
                image_data = self._getByteString(0)
        except Exception as e:
            self._clearError()
            self.__LAST_EXCEPTION = e
        finally:
            self._newPacket()

        return image_data

    def _eval_to_format(self, obj, export_format, **kw):

        res = None
        try:
            self.__LAST_EXCEPTION = None
            self._evaluateExportString(obj, export_format, **kw)
            self.waitForAnswer()
        except MathLinkException as e:
            self._clearError()
            self.__LAST_EXCEPTION = e
            self._newPacket()
            return res

        try:
            ntype = self._getNext()
            tname = self.Env.fromTypeToken(ntype)  # this pattern should maybe be a function...
            if tname == "String":
                res = self._getString()
        except Exception as e:
            self._clearError()
            self.__LAST_EXCEPTION = e
        finally:
            self._newPacket()

        return res

    @property
    def FEServerLink(self):
        return self.__FEServerLink
    @FEServerLink.setter
    def FEServerLink(self, link):
        if not (link is None or isinstance(link, MathLink)):
            raise TypeError("{}: FE link is expected to be None or a MathLink instance but got {}".format(type(self).__name__, type(link).__name__))
        self.__FEServerLink = link

    def __do_call_recursive(self, pkt, call_data = None):
        # I'd prefer not to have this in KernelLink but... not too many options
        # It effectively implements the equivalent of the PJLink ToSymbolicPython
        # but data is efficiently bound to variables to avoid waste

        variable_saved_types = [ BufferedNDArray ]

        if self.use_numpy:
            import numpy
            variable_saved_types.append(numpy.ndarray)
        variable_saved_types=tuple(variable_saved_types)

        if call_data is None and not isinstance(pkt, MLExpr):
            self.Env.logf("Something weird happened {}", pkt)
            return (pkt, )
        elif isinstance(pkt, (float, int, MLSym, MLFunction)):
            self.Env.logf("Got puttable {}", pkt)
            return (pkt, )
        elif isinstance(pkt, str) and len(pkt)<200 and "\n" not in pkt: #basically to handle method names and things...
            self.Env.logf("Got string {}", pkt)
            return (pkt, )
        elif not isinstance(pkt, MLExpr):

            var_name = "{}_{}_{}".format("var", call_data["id"], call_data["vars"])
            call_data["vars"] += 1
            call_data["env"][var_name] = pkt
            self.Env.logf("Storing {} in variable {}", pkt, var_name)

            return (var_name, "variable") #just a way for the thing to realize it's not data...
        elif isinstance(pkt, MLExpr) and pkt.head == "List":

            self.Env.logf("Converting List packet {} to proper list", pkt)
            arg_list = [ self.__do_call_recursive(a, call_data) for a in pkt.args ] # I think this might be the only common one to handle?
            for i, arg in enumerate(arg_list):
                if isinstance(arg, tuple):
                    arg = str(arg[0])
                    arg_list[i] = arg
                elif isinstance(arg, list):
                    arg = ", ".join(arg)
                    arg = "[ " + arg + " ]"
                    arg_list[i] = arg

            return arg_list

        else:
            self.Env.log("Building call")

            top_call = False
            if call_data is None:
                top_call = True
                call_data = {}
                call_data["call"] = ""
                call_data["env"] = {}
                call_data["vars"] = 0
                call_data["id"] = str(id(call_data))
                call_data["indent"] = 0
            # curr = call_data["call"]
            head = pkt.head
            args = pkt.args
            # print(head, args)
            if isinstance(head, MLSym):
                head = head.name
            elif isinstance(head, MLFunction):
                head = head.name

            res = None
            if isinstance(head, str) and head.endswith("PyBlock"):
                indent_level = call_data["indent"]
                block_head = args[2]
                if isinstance(block_head, MLSym) and block_head.name == "Nothing":
                    block_head = None
                elif not isinstance(block_head, str):
                    block_head = self.__do_call_recursive(args[2], call_data)

                try:
                    indent_incr = int(args[1])
                except (TypeError, ValueError):
                    indent_incr = 1

                block_sep = args[2] if isinstance(args[2], str) else self.__do_call_recursive(args[2], call_data)
                arg_list = [ self.__do_call_recursive(a, call_data) for a in args[3].args ]

                arg_list = self.__do_call_recursive(args[0], call_data)

                block_sep = "\n"+block_sep

                to_ind = indent_level + indent_incr
                indent_str = "\t"*to_ind

                arg_list.insert(0, block_head)
                block_string = block_sep.join((indent_str+x for x in arg_list))

                call_data["indent"] = indent_level

                res = block_string

            elif isinstance(head, str) and head.endswith("PyRow"):

                riff = args[1]
                if not isinstance(riff, str):
                    riff = self.__do_call_recursive(riff, call_data)

                arg_list = self.__do_call_recursive(args[0], call_data)

                res = riff.join( arg_list )

            elif head == "Evaluate":

                res = args[0]

            if top_call and head == "CallPacket":

                if isinstance(args[1], MLExpr) and args[1].head == "Evaluate":
                    arg = args[1].args[0]
                else:
                    arg = self.__do_call_recursive(args[1], call_data)

                if isinstance(arg, tuple):
                    arg = arg[0]

                if isinstance(arg, str):
                    res = None
                    self._EXEC_ENV.update(call_data["env"])
                    if len(arg.split("\n", 2)) == 1:
                        try:
                            res = eval(arg, self._EXEC_ENV, self._EXEC_ENV)
                        except SyntaxError:
                            exec(arg, self._EXEC_ENV, self._EXEC_ENV)
                    else:
                        exec(arg, self._EXEC_ENV, self._EXEC_ENV)

                    for k in call_data["env"]:
                        del self._EXEC_ENV[k]
                else:
                    res = arg

                return res

            elif top_call and isinstance(res, str):
                # print(res)
                self._EXEC_ENV.update(call_data["env"])
                if len(res.split("\n", 2)) == 1:
                    try:
                        return eval(res, self._EXEC_ENV, self._EXEC_ENV)
                    except SyntaxError:
                        exec(res, self._EXEC_ENV, self._EXEC_ENV)
                        return None
                else:
                    exec(res, self._EXEC_ENV, self._EXEC_ENV)
                for k in call_data["env"]:
                    del self._EXEC_ENV[k]

            if res is None:
                # print(head)
                raise MathLinkException("UnknownCallType", "couldn't understand packet {}".format(MLExpr(head, args)))
            else:
                return res

    def __callPython(self):
        ### dunno exactly how this data should come through...

        self.Env.log("Getting CallPython packet")

        arg = self.get() ### Call packets take exactly two args? (and the type int has been drained)
        pkt = MLExpr("CallPacket", (1, arg))

        self.Env.logf("Calling python on packet {}", pkt)

        # try:
        res = self.__do_call_recursive(pkt)
        if res is None:
            self._putSymbol("Null")
        else:
            self.put(res)

        # except Exception as e:
        #     import traceback as tb
        #     self.__LAST_EXCEPTION_DURING_CALL_HANDLING = e
        #     self.put(self.M.F(self.M.PackageContext+"PythonTraceback", tb.format_exc()))
        #     self._clearError()
        # finally: # is this wise?
        #     self._endPacket()


    def __connectToFEServer(self, timeout = 100):
        import time
        res = False
        fe = None
        try:
            linkName = self._getString().strip()
            protocol = self._getString().strip()
            mlargs   = "-linkmode connect -linkname " + linkName
            if len(protocol) > 0:
                mlargs += " -linkprotocol " + protocol
            fe = MathLink(mlargs)
            # Do nothing if link open fails. Return value of "False" will be sufficient to indicate this,
            # although I cannot currently distinguish between "link open failed" and "problem during link setup".
            try:
                fe.connect()
                fe.put(self.M.InputNamePacket("In[1]:="))
                fe.flush()
                startTime = time.time()
                if timeout is not None:
                    timeout = 1000 * timeout
                while timeout is None or time.time() - startTime < timeout:
                    f = fe._getFunction()
                    fe._newPacket()
                    if f.name == "EnterTextPacket" or f.name == "EnterExpressionPacket":
                        res = True
                        break
                    elif f.name == "EvaluatePacket":
                        fe.put(self.M.ReturnPacket(MLSym("Null")))
                    else:
                        pass
                else:
                    raise MathLinkException("ConnectTimeout")
            except MathLinkException as e:
                fe.close()
                fe = None
        except Exception as e:
            self.__handleCleanException(e)

        self.__FEServerLink = fe
        self.put(self.M.ReturnPacket(res, _EndPacket=True))

    def __disconnectToFEServer(self):
        fe = self.__FEServerLink
        if fe is not None:
            fe.close()
            self. __FEServerLink = None
            self.put(self.M.ReturnPacket(MLSym("Null"), _EndPacket=True))

###############################################################################################
#                                                                                             #
#                                     WrappedKernelLink                                       #
#                                                                                             #
###############################################################################################

class WrappedKernelLink(KernelLink):
    """WrappedKernelLink is the only full implementation of KernelLink in J/Link. The idea is to implement KernelLink
    by "wrapping" a MathLink instance, which is responsible for all the transport-specific details. In other
    words, if you give me a MathLink implementation, I can create a KernelLink implementation by simply doing:

    KernelLink kl = new WrappedKernelLink(theMathLink);

    This is exactly what happens in MathLinkFactory when createKernelLink is called. In this way, new KernelLinks
    can be created that use new transport mechanisms (like RMI and HTTP instead of native MathLink) simply by writing
    a MathLink implementation that uses the mechanism and then supplying this MathLink instance to WrappedKernelLink.
    All of the KernelLink-specific implementation is inherited from KernelLinkImpl. The only thing here is the
    implementation of the MathLink interface by forwarding calls to a "wrapped" MathLink instance.

    The philosophy is to let the WrappedKernelLink class maintain user state associated with the link (the identity of
    the Complex class, the user yielder, the user message handler, etc.) This state is part of MathLink, so both
    the WrappedKernelLink and the wrapped MathLink could contain it. It is much more sensible to have it all
    held here and only forward non-state-dependent MathLink calls to the wrapped MathLink. For example, we don't
    forward putComplex() or getComplex().
    """

    def __init__(self, link = None):
        self.__USE_NUMPY = None
        self.__link_connected = False
        self.__impl = link

        if isinstance(link, MathLink):
            self.__impl = link
            self.addMessageHandler(self._messageHandler) ##

        super().__init__()

    def __ensure_connection(self):
        import time
        if not self.__link_connected:
            # time.sleep(.5) # I guess the kernel has to start up or else things lock?
            self.connect()
            if self.__link_connected:
                time.sleep(1)

    def close(self):
        # self.__ensure_connection()
        return self.__impl.close()

    def connect(self, timeout=None):
        self.__link_connected = self.__impl.connect(timeout=timeout)
        return self.__link_connected

    @property
    def link_number(self):
        # self.__ensure_connection()
        return self.__impl.link

    @property
    def name(self):
        # self.__ensure_connection()
        return self.__impl.name

    def _newPacket(self):
        # self.__ensure_connection()
        return self.__impl._newPacket()

    def _endPacket(self):
        # self.__ensure_connection()
        return self.__impl._endPacket()

    def _error(self):
        # self.__ensure_connection()
        return self.__impl._error()

    def _clearError(self):
        # self.__ensure_connection()
        return self.__impl._clearError()

    def _setError(self, err):
        # self.__ensure_connection()
        return self.__impl._setError(err)

    def _errorMessage(self):
        # self.__ensure_connection()
        return self.__impl._errorMessage()

    @property
    def use_numpy(self):
        # self.__ensure_connection()
        return self.__impl.use_numpy

    @use_numpy.setter
    def use_numpy(self, val):
        self._setUseNumPy(val)

    def _setUseNumPy(self, val):
        use = bool(val)
        self.__USE_NUMPY = use
        self.__impl._setUseNumPy(use)

    def _getUseNumPy(self):
        return self.__impl._getUseNumPy()

    def _setDebugLevel(self, lvl):
        return self.__impl._setDebugLevel(lvl)

    @property
    def ready(self):
        # self.__ensure_connection()
        return self.__impl.ready

    def flush(self):
        # self.__ensure_connection()
        return self.__impl.flush()

    def _putNext(self, otype):
        # self.__ensure_connection()
        return self.__impl._putNext(otype)

    def _getArgCount(self):
        self.__ensure_connection()
        return self.__impl._getArgCount()

    def _putArgCount(self, argCount):
        # self.__ensure_connection()
        return self.__impl._putArgCount(argCount)

    def _putSize(self, s):
        # self.__ensure_connection()
        return self.__impl._putSize(s)

    def _bytesToPut(self):
        self.__ensure_connection()
        return self.__impl._bytesToPut()

    def _bytesToGet(self):
        self.__ensure_connection()
        return self.__impl._bytesToGet()

    def _putData(self, data, num=None):
        # self.__ensure_connection()
        return self.__impl._putData(data, num)

    def _getData(self, num):
        self.__ensure_connection()
        return self.__impl._getData(num)

    def _getString(self):
        self.__ensure_connection()
        return self.__impl._getString()

    def _getByteString(self, missing = 0):
        self.__ensure_connection()
        return self.__impl._getByteString(missing)

    def _putByteString(self, data, num=None):
        # self.__ensure_connection()
        return self.__impl._putByteString(data)

    def _putSymbol(self, s):
        # self.__ensure_connection()
        return self.__impl._putSymbol(s)

    def _putDouble(self, s):
        # self.__ensure_connection()
        return self.__impl._putDouble(s)

    def _putInt(self, s):
        # self.__ensure_connection()
        return self.__impl._putInt(s)

    def _putString(self, s):
        # self.__ensure_connection()
        return self.__impl._putString(s)

    def _putBool(self, s):
        self.__ensure_connection()
        return self.__impl._putBool(s)

    def put(self, o):
        self.__ensure_connection()
        if isinstance(o, type):
            self.Env.log("Putting repr of type {} on link", o.__name__)
            return self.__impl.put(repr(o))
        else:
            try:
                return self.__impl.put(o)
            except Exception as e:
                import traceback as tb
                self.Env.log(tb.format_exc())
                return self.__impl.put(repr(o))

    def _getInt(self):
        self.__ensure_connection()
        return self.__impl._getInt()

    def _getLong(self):
        self.__ensure_connection()
        return self.__impl._getLong()

    def _getDouble(self):
        self.__ensure_connection()
        return self.__impl._getDouble()

    def _getByte(self):
        self.__ensure_connection()
        return self.__impl._getByte()

    def _getChar(self):
        self.__ensure_connection()
        return self.__impl._getChar()

    def _getFloat(self):
        self.__ensure_connection()
        return self.__impl._getFloat()

    def _getShort(self):
        self.__ensure_connection()
        return self.__impl._getShort()

    def _getSymbol(self):
        self.__ensure_connection()
        return self.__impl._getSymbol()

    def _getFunction(self):
        self.__ensure_connection()
        return self.__impl._getFunction()

    def _putFunction(self, f, argCount):
        # self.__ensure_connection()
        return self.__impl._putFunction(f, argCount)

    def _checkFunction(self, f, argCount=None):
        self.__ensure_connection()
        return self.__impl._checkFunction(f, argCount)

    def transferExpression(self, source):
        self.__ensure_connection()
        return self.__impl.transferExpression(source)

    def transferToEndOfLoopbackLink(self, source):
        self.__ensure_connection()
        return self.__impl.transferToEndOfLoopbackLink(source)

    def _getExpr(self):
        self.__ensure_connection()
        return self.__impl._getExpr()

    def peek(self):
        self.__ensure_connection()
        return self.__impl.peek()

    def _getMessage(self): #wut?
        self.__ensure_connection()
        return self.__impl._getMessage()

    def _putMessage(self, msg):
        self.__ensure_connection()
        return self.__impl._putMessage(msg)

    def _messageReady(self): #huh?
        return self.__impl._messageReady()

    def _createMark(self):
        self.__ensure_connection()
        return self.__impl._createMark()

    def _seekMark(self, mark):
        self.__ensure_connection()
        return self.__impl._seekMark(mark)

    def _destroyMark(self, mark):
        self.__ensure_connection()
        return self.__impl._destroyMark(mark)

    def _setYieldFunctionOn(self, target, meth):
        # self.__ensure_connection()
        return self.__impl._setYieldFunctionOn(target, meth)

    def _addMessageHandlerOn(self, target, meth):
        # self.__ensure_connection()
        return self.__impl._addMessageHandlerOn(target, meth)

    def _wrap(self, checkLink = True, checkError = True, check = None, lock = True):
        return self.__impl._wrap(checkLink, checkError, check, lock)

    def _nextPacket(self):
        # Code here is not just a simple call to impl.nextPacket(). For a KernelLink, nextPacket() returns a
        # wider set of packet constants than the MathLink C API itself. We want nextPacket() to work on the
        # non-packet types of heads the kernel and FE send back and forth.
        # Because for some branches below we seek back to the start before returning, it is not guaranteed
        # that when nextPacket() returns, the current packet has been "opened". Thus it is not safe to write
        # a J/Link program that loops calling nextPacket()/newPacket(). You need to call handlePacket() after
        # nextPacket() to ensure that newPacket() will throw away the curent "packet".

        # createMark will fail on an unconnected link, and the user might call this
        # before any reading that would connect the link.
        # self.__ensure_connection()

        pkt = None
        mark = self._createMark()
        try:
            pkt = self.__impl._nextPacket()
        except MathLinkException as e:
            if e.name == "UnknownPacket":
                self._clearError()
                self._seekMark(mark)
                f = self._getFunction()
                if f.name == "ExpressionPacket":
                    pkt = self.Env.getPacketInt("Expression")
                elif f.name == "BoxData":
                    self._seekMark(mark)
                    pkt = self.Env.getPacketInt("Expression")
                else:
                    # Note that all other non-recognized functions get labelled as FEPKT. I could perhaps be
                    # more discriminating, but then I risk not recognizing a legitimate communication
                    # intended for the front end. This means that FEPKT is not a specific indication that
                    # a front-end-related packet is on the link. Because there is no diagnostic packet head,
                    # we need to seek back to before the function was read. That way, when programs call
                    # methods to read the "contents" of the packet, they will in fact get the whole thing.
                    self._seekMark(mark)
                    pkt = self.Env.getPacketInt("FE")
            else:
                raise
        finally:
            self._destroyMark(mark)

        return pkt

    def _getNext(self):
        res = self.__impl._getNext()
        name = self.Env.fromTypeToken(res)
        if name == "Symbol" and self._nextIsObject():
            res = self.Env.toTypeToken("Object")
        return res

    def _getType(self):
        self.__ensure_connection()
        res = self.__impl._getType()
        name = self.Env.fromTypeToken(res)
        if name == "Symbol" and self._nextIsObject():
            res = self.Env.toTypeToken("Object")
        return res

    def _getArray(self, otype, depth, headList=None):
        # This method could be left out of this class, instead relying on the superclass (KernelLinkImpl) implementation.
        # But that would eventually trickle down to the inefficient "catch-all" array-getting code in MathLinkImpl.
        # On the assumption that the wrapped link can do some array types more efficiently, we forward those to it.
        # In the common case where the wrapped link is a NativeLink, this assumption holds true for types that are
        # native in the MathLink C API.

        # The only types we must handle ourselves are TYPE_COMPLEX (since we must be sure to use _our_ notion of the                                                                                                         // complex class, not the impl's, which will not even have been set), and TYPE_OBJECT (because only a
        # KernelLink can do that).
        typename = self.Env.fromTypeInt(otype, "typename")
        if typename == "Object":
            return super()._getArray(otype, depth, headList)
        else:
            # We don't _need_ to forward--just an optimization.
            return self.__impl._getArray(otype, depth, headList)

    def _putArray(self, o, headList = None):
        try:
            arr, tint, dims, depth = self._get_put_array_params(o)
            # if it worked arr is in efficient form so this is fine
            self.__impl._putArray(o, headList = None)
        except (ValueError, TypeError) as e:
            import traceback as tb
            self.Env.log(tb.format_exc())
            self._putArrayPiecemeal(o, headList, 0)