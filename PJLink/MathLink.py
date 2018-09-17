"""The MathLink module provides the LinkBase abstract base class and the MathLink concrete implementation
Generally these will both only serve as further base classes for other classes
"""
from abc import *
from .MathLinkExceptions import *
from .MathLinkEnvironment import MathLinkEnvironment as Env
from .HelperClasses import *

###############################################################################################
#                                                                                             #
#                                           LinkBase                                          #
#                                                                                             #
###############################################################################################

class LinkBase(ABC):
    """The base class for working with Links. It serves as an abstract layer for which MathLink is a concrete implementation.
    """

    Env = Env  # just a reference so that it can be referenced outside the package
    Util = ArrayUtils

    @abstractmethod
    def close(self):
        """Closes the link. Always call close() on every link when you are done using it.
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def connect(self, timeout=None):
        """Connects the link, if it has not already been connected. There is a difference between opening a link (which is what the MathLinkFactory methods createLink() and createKernelLink() do) and connecting it, which verifies that it is alive and ready for data transfer.
All the methods that read from the link will connect it if necessary. The connect() method lets you deliberately control the point in the program where the connection occurs, without having to read anything.
        :param timeout:
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def name(self):
        """Gives the name of the link. For typical links, the name of a listen-mode link can be used by the other side to connect to.
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _newPacket(self):
        """Discards the current packet, if it has been partially read. Has no effect if the previous packet was fully read.
This is a useful cleanup function. You can call it when you are finished examining the contents of a packet that was opened with nextPacket() or waitForAnswer(), whether you have read the entire packet contents or not. You can be sure that the link is then in a state where you are ready to read the next packet.
It is also frequently used in a catch block for a MathLinkException, to clear off any unread data in a packet before returning to the normal program flow.
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _nextPacket(self):
        """"Opens" the next packet arriving on the link. It is an error to call nextPacket() while the current packet has unread data; use newPacket() to discard the current packet first.
Most programmers will use this method rarely, if ever. J/Link provides higher-level functions in the KernelLink interface that hide these low-level details of the packet loop.
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _endPacket(self):
        """Call it when you are finished writing the contents of a single packet.
Calling endPacket() is not strictly necessary, but it is good style, and it allows J/Link to immediately generate a MathLinkException if you are not actually finished with writing the data you promised to send.
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _error(self):
        """Gives the code corresponding to the current error state of the link.
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _clearError(self):
        """Clears the link error condition, if possible. After an error has occurred, and a MathLinkException has been caught, you must call clearError() before doing anything else with the link.
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _errorMessage(selfs):
        """Gives a textual message describing the current error.
        :return:
        """

    @abstractmethod
    def _setError(self, err):
        """Sets the link's error state to the specified value. Afterwards, error() will return this value. Very few programmers will have any need for this method.
        :param err:
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def ready(self):
        """Indicates whether the link has data waiting to be read. In other words, it tells whether the next call that reads data will block or not.
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def flush(self):
        """Immediately transmits any data buffered for sending over the link.
Any calls that read from the link will flush it, so you only need to call flush() manually if you want to make sure data is sent right away even though you are not reading from the link immediately. Calls to ready() will not flush the link, so if you are sending something and then polling ready() waiting for the result to arrive (as opposed to just calling nextPacket() or waitForAnswer()), you must call flush to ensure that the data is sent.
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _getNext(self):
        """Gives the type of the next element in the expression currently being read.
To check the type of a partially read element without advancing to the next element, use getType().
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _getType(self):
        """Gives the type of the current element in the expression currently being read.
Unlike getNext(), getType() will not advance to the next element if the current element has only been partially read.
        :return:
        """
        raise NotImplemented

    def _getTypeName(self):
        """Gives the name of the type of the current element in the expression currently being read. Builds off of _getType

        :return:
        """

        return self.Env.fromTypeToken(self._getType())

    @abstractmethod
    def _putNext(self, otype):
        """Identifies the type of data element that is to be sent.
putNext() is rarely needed. The two most likely uses are to put expressions whose heads are not mere symbols (e.g., Derivative[2][f]) or to put data in textual form. Calls to putNext() must be followed by putSize() and putData(), or by putArgCount() for the MLTKFUNC type. Here is how you could send Derivative[2][f]:

 ml.putNext(MathLink.MLTKFUNC);  // The func we are putting has head Derivative[2], arg f
 ml.putArgCount(1);  // this 1 is for the 'f'
 ml.putNext(MathLink.MLTKFUNC);  // The func we are putting has head Derivative, arg 2
 ml.putArgCount(1);  // this 1 is for the '2'
 ml.putSymbol("Derivative");
 ml.put(2);
 ml.putSymbol("f");
        :param otype:
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _getArgCount(self):
        """Reads the argument count of an expression being read manually.
This method can be used after getNext() or getType() returns the value MLTKFUNC. The argument count is always followed by the head of the expression. The head is followed by the arguments; the argument count tells how many there will be.
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _putArgCount(self, argCount):
        """Specifies the argument count for a composite expression being sent manually.
Use it after a call to putNext() with the MLTKFUNC type.
        :param argCount:
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _putSize(self, size):
        """Specifies the size in bytes of an element being sent in textual form.
A typical sequence would be putNext(), followed by putSize(), then putData().
        :param size:
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _bytesToPut(self):
        """Gives the number of bytes that remain to be sent in the element that is currently being sent in textual form.
After you have called putSize(), the link knows how many bytes you have promised to send. This method lets you determine how many you still need to send, in the unlikely event that you lose track after a series of putData() calls.
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _bytesToGet(self):
        """Returns the number of bytes that remain to be read in the element that is currently being read in textual form.
Lets you keep track of your progress reading an element through a series of getData() calls.
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _putData(self, data, num=None):
        """Used for sending elements in textual form. After calling putNext() and putSize(), a series of putData() calls are used to send the actual data.
The so-called "textual" means of sending data is rarely used. Its main use is to allow a very large string to be sent, where the string data is not held in a single String object. The most important use of this technique in the C-language MathLink API was to send integers and reals that were too large to fit into an int or double. This use is unnecessary in J/Link, since Java has BigInteger and BigDecimal classes, and these objects can be sent directly with put().
        :param data:
        :param num:
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _getData(self, num):
        """Gets a specified number of bytes in the textual form of the expression currently being read. The returned array will have a length of at most len.
You can use bytesToGet() to determine if more getData() calls are needed to completely read the element.
        :param num:
        :return:
        """
        raise NotImplemented

    # We drop support for all the specialized JLink functions because they obviously don't do
    # much for python

    @abstractmethod
    def put(self, obj):
        """Sends a data value -- lack of overloading will cause this to differ from the JLink case
        :param obj:
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def get(self):
        """Gets a data value -- this is possible because of python type flexibility
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def peek(self):
        """Creates an Expr from the current expression, but does not drain it off the link.
Like getExpr(), but peekExpr() does not actually remove anything from the link. In other words, it leaves the link in the same state it was in before peekExpr() was called.
        :return:
        """
        raise NotImplemented

    # Not sure to what degree this should remain...

    @abstractmethod
    def _getFunction(self):
        """Reads a function name and argument count.
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _putFunction(self, f, argCount):
        """Sends a function name and argument count.
Follow this with calls to put the argument
        :param f:
        :param argCount:
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _checkFunction(self, f, argCount=None):
        """Sends a function name and argument count.
Follow this with calls to put the argument
        :param f:
        :param argCount:
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def transferExpression(self, source):
        """Writes a complete expression from the link source to this link.
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def transferToEndOfLoopbackLink(self, source):
        """Writes the entire contents of the LoopbackLink source to this link.
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _createMark(self):
        """Creates a mark at the current point in the incoming MathLink data stream.
Marks can returned to later, to re-read data. A common use is to create a mark, call some method for reading data, and if a MathLinkException is thrown, seek back to the mark and try a different method of reading the data.

Make sure to always call destroyMark() on any marks you create. Failure to do so will cause a memory leak.

Some of the usefulness of marks in the C-language MathLink API is obviated by J/Link's Expr class.

        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _seekMark(self, mark):
        """Resets the current position in the incoming MathLink data stream to an earlier point.

        :param mark:
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def _destroyMark(self, mark):
        """Destroys a mark. Always call destroyMark() on any marks you create with createMark().

        :param mark:
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def setYieldFunction(self, meth):
        """Sets the Java method you want called as a yield function.
The method must be public and its signature must be (V)Z (e.g., public boolean foo()). You can pass null for cls if obj is provided. If the method is static, pass null as obj.

Yield functions are an advanced topic, and are discussed in greater detail in the User Guide. Few users will need to use one.

        :param meth:
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def addMessageHandler(self, meth):
        """Specifies the Java method you want called as a message handler.
Do not confuse this type of message, used mainly for communicating requests to interrupt or abort a computation, with Mathematica warning and error messages, which are unrelated.

The method you specify will be added to the set that are called whenever a MathLink message is received by your Java program. The method must be public and its signature must be (II)V (e.g., public void foo(int msgType, int ignore)). You can pass null for cls if obj is provided. If the method is static, pass null for obj. The first argument passed to your function when it is called is the integer code giving the message type (e.g., MLABORTMESSAGE, MLINTERRUPTMESSAGE, etc.) The second argument is undocumented and should be ignored.

Do not attempt to use the link from within your message handler function.

You can set more than one message handler, hence the name "addMessageHandler".

Message handlers are an advanced technique. Few programmers will need to use one.

        :param meth:
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def removeMessageHandler(self, meth):
        """Removes a message handler you previously set up with addMessageHandler.
Do not confuse this type of message, used mainly for communicating requests to interrupt or abort a computation, with Mathematica warning and error messages, which are unrelated.

Message handlers are an advanced topic, and are discussed in greater detail in the User Guide. Few users will need to use one.

        :param meth:
        :return:
        """
        raise NotImplemented

###############################################################################################
#                                                                                             #
#                                      MathLinkImplBase                                       #
#                                                                                             #
###############################################################################################


class MathLinkImplBase(LinkBase):
    """MathLinkImplBase is intended to hold all state-independent implementation of MathLink logic. This implies that
there will be no non-static fields in this class.  Examples of things that cannot go here are some aspects
of Complex handling (requires holding state in the form of the complex class) and yielder/message stuff
(requires holding yield/msg function references).

The motivation for splitting up the original MathLinkImpl into a state-independent MathLinkImplBase and a
state-dependent MathLinkImpl was that it was felt that there might be future implementations of MathLink
that would handle state in different ways and thus would want to be able to inherit from MathLinkImplBase and
be guaranteed that no references to state variables would occur in any of its logic. This reasoning now seems less
relevant, but perhaps some maintainability benefits will accrue with the split."""

    def peek(self):
        mark = self._createMark()
        try:
            expr = self._getExpr()
        except MathLinkException as e:
            expr = None
        finally:
            self._seekMark(mark)
            self._destroyMark(mark)
        return expr

    _getter_map = {
        "Boolean"    : "Bool",
        "Byte"       : "Byte",
        "Char"       : "Char",
        "Short"      : "Short",
        "Integer"    : "Int",
        "Long"       : "Long",
        "Float"      : "Float",
        "Double"     : "Double",
        "String"     : "String",
        "BigInteger" : "Int",
        "Decimal"    : "Decimal",
        "Expr"       : "Expr",
        "Complex"    : "Complex"
    }

    @abstractmethod
    def _getSymbol(self):
        raise NotImplemented
    @abstractmethod
    def _getChar(self):
        raise NotImplemented
    @abstractmethod
    def _getString(self):
        raise NotImplemented
    def _getExpr(self):
        return Expr.createFromLink(self)
    @abstractmethod
    def _getByte(self):
        raise NotImplemented
    @abstractmethod
    def _getByteString(self, missing):
        raise NotImplemented
    @abstractmethod
    def _getShort(self):
        raise NotImplemented
    @abstractmethod
    def _getInt(self):
        raise NotImplemented
    @abstractmethod
    def _getLong(self):
        raise NotImplemented
    @abstractmethod
    def _getFloat(self):
        raise NotImplemented
    @abstractmethod
    def _getDouble(self):
        raise NotImplemented
    def _getComplex(self):
        otype = self._getNext()
        strtype = self.Env.fromTypeToken(otype)
        if strtype == 'int' or strtype == 'real':
            rePart = self._getDouble()
            imPart = 0
        elif strtype == 'func' and self._checkFunction("Complex", 2):
            rePart = self._getDouble()
            imPart = self._getDouble()
        else:
            raise MathLinkException("BadComplex")
        return complex(rePart, imPart)
    def _getDecimal(self):
        from decimal import Decimal as decimal
        s = self._getString()
        return decimal(s)
    #@abstractmethod
    def _getBool(self):
        s = self._getSymbol()
        res = None
        if s == "True":
            res  = True
        elif s == "False":
            res = False
        return res

    def _getSingleObject(self, otype, *params):
        """Gets a single object of type otype off the link

        :param otype:
        :return:
        """

        meth = None
        if isinstance(otype, str):
            try:
                meth = getattr(self, "_get"+otype)
            except AttributeError:
                pass

        for k in (otype, self.Env.fromTypeInt(otype, "typename"), self.Env.fromTypeToken(otype)):
            try:
                meth = self._getter_map[k]
            except KeyError:
                pass
            else:
                meth = getattr(self, "_get"+meth)
                break

        res = None
        if meth is not None:
            res = meth(*params)

        return res

    def get(self):
        # sub cases of the KernelLink one

        res = None
        t1 = self._getTypeName()
        if t1 == "Integer":
            t = self._getInt()
            t_flint = self.Env.toTypeInt("FloatOrInt")
            t_dubint = self.Env.toTypeInt("DoubleOrInt")
            t_float = self.Env.toTypeInt("Float")
            t_dub = self.Env.toTypeInt("Double")
            arr_int = self.Env.toTypeInt("Array1D")
            if t % arr_int == t_flint:
                t = t_float + arr_int * ( t // arr_int )
            elif t % arr_int == t_dubint:
                t = t_dub + arr_int * ( t // arr_int )

            if t == t_dubint:
                t = t_dub
            elif t == t_flint:
                t = t_float

            try:
                res = self._getSingleObject(t)
            except (MathLinkException, ValueError, TypeError):
                pass # Maybe I should handle these?

            # I have unfortunately not wholly faithfully handled this...
            # hopefully I can come back and do so sometime

            if res is None:
                for r in range(2, 10):
                    tar = self.Env.toTypeInt("Array{}D".format(r))
                    if t > tar:
                        res = self._getArray(t - tar, r - 1)

        else:
            res = self._getSingleObject(t1)

        return res


    def _getArray(self, otype, depth, headList=None):
        """Can handle here the cases where high-level mathlink work is required. The implementation in
derived classes (e.g., NativeLink) should handle other cases (for NativeLink, those are the cases
that are handled by a single call into the native library). It is safe to call this implementation
from derived classes for depth > 1 arrays (in which case it handles the logic of breaking up the
read into slices at the last dimension), or arrays of any depth of types that cannot be more efficiently done
by more direct methods (specifically, STRING, BOOLEAN, LONG, BIGDECIMAL, BIGINTEGER, EXPR, COMPLEX).

        :param otype:
        :param depth:
        :param heads:
        :return:
        """
        result = None
        if depth == 1:
            func, arg_count = self._getFunction()
            result = [ self._getSingleObject(otype) for i in range(arg_count) ]
            if headList is not None:
                headList[0] = func
        else:
            result = self._getArraySlices(otype, depth, headList, 0, None)

        return result

    def _getArraySlices(self, otype, depth, heads = None, headsIndex = 0, componentClass = None):
        """This method for reading arrays recursively walks down the levels, calling back to getArray to get the last level
(which are 1-D arrays).
        :param otype:
        :param depth:
        :param heads:
        :param headsIndex:
        :param componentClass:
        :return:
        """

        res_array = None
        if depth>1:

            res_array = [ None ] * depth
            func, arg_count = self._getFunction()
            if heads is not None:
                if isinstance(heads, list):
                    heads[ headsIndex ] = func
                else:
                    heads = [ func ]

            for i in range(arg_count):
                res_array[i] = self._getArraySlices(type, depth - 1, heads, headsIndex + 1, None)

        else:
            # depth == 1. Call back to getArray to do the actual work of reading from the link.
            # Here is the ugliness of calling the getArray(Class, ...) method that is only publicly
            # declared in KernelLink. Because we can get down this far on object arrays, we need access
            # to the API method that allows us to specify the object type. The implementation in this class
            # does nothing (it throws an exception), but only a KernelLinkImpl instance will ever cause the
            # branch to be executed, and KernelLinkImpl overrides that method. The if() test here is basically
            # type == TYPE_OBJECT, without explicitly referring to the KernelLink.TYPE_OBJECT constant.

            head_holder = ['']
            if self.Env.fromTypeInt(otype) == object:
                res_array = self._getArray(componentClass, 1, head_holder)

            else:
                res_array = self._getArray(componentClass, 1, head_holder)

            if heads is not None:
                heads[headsIndex] = head_holder[0]

        return res_array

    # This is just a pile of functions that are abstractly defined but which implement
    # the most basic data passing to Mathematica
    @abstractmethod
    def _putSymbol(self, s):
        raise NotImplemented
    @abstractmethod
    def _putString(self, s):
        raise NotImplemented
    def _putExpr(self, e):
        e.put(self)
    def _putComplex(self, c):
        try:
            real = c.real
            imag = c.imag
        except:
            self._putSymbol("$Failed")
        else:
            self._putFunction("Complex", 2)
            self.put(real)
            self.put(imag)
    @abstractmethod
    def _putInt(self, i):
        raise NotImplemented
    #@abstractmethod
    def _putFloat(self, f):
        return self._putDouble(f)
    @abstractmethod
    def _putDouble(self, f):
        raise NotImplemented
    @abstractmethod
    def _putBool(self, b):
        raise NotImplemented
    #@abstractmethod
    def _putChar(self, c):
        return self._putInt(c)
    #@abstractmethod
    def _putShort(self, h):
        return self._putInt(h)
    #@abstractmethod
    def _putLong(self, l):
        return self._putLong(l)
    def _putNone(self, none = None):
        return self._putSymbol("Null")
    @abstractmethod
    def _putArray(self, o, headList = None):
        raise NotImplemented
    def _putMLFunction(self, call):
        self._putFunction(call.head, call.argCount)
    @abstractmethod
    def _putByteString(self, data, num=None):
        raise NotImplemented
    def _putMLExpr(self, call):
        self._putMLFunction(MLFunction(call.head, len(call.args)))
        for a in call.args:
            self.put(a)
        if call.end:
            self._endPacket()
    def _putMLSym(self, sym):
        self._putSymbol(sym.name)

    from decimal import Decimal as decimal
    from fractions import Fraction as fraction
    _putter_map = {
        bool       : 'Bool',
        str        : 'String',
        complex    : 'Complex',
        int        : 'Int',
        float      : 'Float',
        Expr       : "Expr",
        decimal    : "Decimal",
        fraction   : "Rational",
        MLExpr     : "MLExpr",
        MLFunction : "MLFunction",
        MLSym      : "MLSym",
        bytes      : "ByteString",
        bytearray  : "ByteString"
    }
    del decimal
    del fraction

    def _getPutter(self, o):

        putter = None
        if o is None:
            putter = self._putNone
        else:
            try:
                type_name = o["TypeName"]
                putter = getattr(self, '_put'+type_name)
            except:
                for key, val in self._putter_map.items():
                    if isinstance(o, key):
                        putter = getattr(self, '_put'+val)
                        break
                else:
                   try:
                       it = iter(o) # check if is iterable
                       putter = self._putArray
                   except:
                       putter = None#self._putSingleObject # Dunno what the fallback should be
        return putter

    def put(self, o):
        """Concrete implementation of general put structure

        :param o:
        :return:
        """
        putter = self._getPutter(o)
        self.Env.logf("delegating put to {}", putter)
        return putter(o)

    def _putArrayPiecemeal(self, o, heads = None, head_index = 0):
        """Calls put for each piece of o. Inefficient fallback, effectively.

        :param o:
        :param heads:
        :param head_index:
        :return:
        """

        head = heads[head_index] if heads is not None else None
        if not isinstance(head, str):
            head = "List"

        try:
            olen = len(o)
        except TypeError:
            olen = 0

        if olen > 0:
            self._putFunction(head, olen)
            head_index += 1
            for ob in o:
                self._putArrayPiecemeal(ob, heads, head_index)
        else:
            self.put(o)

class MathLink(MathLinkImplBase):
    """The step right below MathLink implementation wise

    """

    import threading

    __userYielder = None
    __yielderObject = None
    __yieldFunctionLock = threading.RLock()

    __userMsgHandlers = [ ] # we use a list rather than set because hashability might be important here

    __timeoutMillis = None
    __startConnectTime = 0
    __connectTimeoutExpired = False

    __packetListeners = [ ]# we use a list rather than set because hashability might be important here
    __packetListenerLock = threading.RLock()

    def _connect_timeout(self, timeout):
        import math, time
        self.setYieldFunction(self._connectTimeoutYielder)
        self.__timeoutMillis = math.floor(timeout)
        self.__connectTimeoutExpired = False
        self.__startConnectTime = math.floor(time.time())
        try:
            self._connect()
        finally:
            # Clears the C-to-Python callback completely.
            self.setYieldFunction(None)

        # If the connectTimeoutYielder ever returns true, then either the link will die and the
        # connect() call above will throw a fatal MathLinkException, or connect() will fail but not
        # throw because the "deferred connection" error that is returned is not deemed to be
        # exception-worthy in general. Here, we want to throw an exception on that error, so we
        # make up our own.
        if self.__connectTimeoutExpired:
            raise MathLinkException("ConnectTimeout")

    def connect(self, timeout=None):
        if timeout is not None and timeout > 0:
            self._connect_timeout(timeout)
        else:
            self._connect()
        return True

    @property
    def name(self):
        return self._name()

    @property
    def ready(self):
        return self._ready()

    @abstractmethod
    def _getMessage(self):
        raise NotImplemented
    @abstractmethod
    def _putMessage(self, msg):
        raise NotImplemented
    @abstractmethod
    def _messageReady(self):
        raise NotImplemented

    # YieldFunction and MessageHandler stuff here. Note that implementing link classes
    # will likely need to override some of these methods and provide some implementation of their own.
    # What we can do here is manage the Java-level portions (like handling the list of message
    # handlers, or the user-supplied Java yield function). See NativeLink for an example of
    # what a derived class might need to do.

    def _setYieldFunctionOn(self, target, meth):
        # Convenient to set a yielder while a thread is blocking in MathLink. Thus, this method is not synchronized.
        # Instead, we synch on an object that is specific to the yielder-handling data structures.
        with self.__yieldFunctionLock:
            self.__userYielder = None
            self.__yielderObject = None
            if meth is not None:
                self.__userYielder = meth
                self.__yielderObject = target

    def setYieldFunction(self, meth):
        self._setYieldFunctionOn(self, meth)

    def _addMessageHandlerOn(self, target, meth):
        # This sets the method that will be called in messageCallback.
        # First, check to see if meth is already in there.
        mrec = MsgHandlerRecord(meth, target)
        for md in self.__userMsgHandlers:
            if md.method == mrec.method and md.target == mrec.target:
                break
        else:
            self.__userMsgHandlers.append(mrec)

    def addMessageHandler(self, meth):
        self._addMessageHandlerOn(self, meth)

    def removeMessageHandler(self, meth):
        # This sets the method that will be called in messageCallback.
        # First, check to see if meth is already in there.

        call_again = False
        for md in self.__userMsgHandlers:
            call_again = (md["method"] == meth)
            if md["method"] == meth:
                self.__userMsgHandlers.remove(md)
                break

        if call_again:
            self.removeMessageHandler(meth)

    def _messageCallback(self, message, n):
        """Provides a call back for messages

        :param message:
        :param n:
        :return:
        """

        for handler in self.__userMsgHandlers:
            try:
                handler["method"](handler["target"], message, n)
            except Exception as e:
                import traceback as tb
                tb.print_exc()

    def _yielderCallback(self):
        """Provides a call back for yield functions

        :param message:
        :param n:
        :return:
        """

        with self.__yieldFunctionLock:
            try:
                res = self.__userYielder(self.__yielderObject)
            except Exception as e:
                import traceback as tb
                tb.print_exc()
                res = False

        return True if res else False

    def _connectTimeoutYielder(self):
        import time
        self.__connectTimeoutExpired = time.time() > self.__startConnectTime + self.__timeoutMillis
        return self.__connectTimeoutExpired

    # Note that the PacketListener support methods are declared in KernelLink, not MathLink.
    # But it is convenient to put their implementation here. For MathLink implementation classes
    # that subclass this, no harm done, since the methods are not visible through those object's
    # types (MathLink). KernelLink classes can share this implementation without us
    # having to create a new abstract class slightly fatter than MathLinkImpl that implements
    # KernelLink but only adds these three methods. Design-wise, KernelLinkImpl is really too fat
    # to have these methods in it. There are some KernelLink implementations that want everything
    # in MathLinkImpl, but not everything in KernelLinkImpl (such as all the support for passing
    # object references). An example is KernelLink_HTTP, which needs MathLinkImpl + packetHandler
    # only. Rather than create a new abstract class between MathLinkImpl and KernelLinkImpl, I'll
    # just toss these here. Note one hack as a consequence--the cast to KernelLink in the
    # PacketArrivedEvent constructor.

    def addPacketListener(self, listener):
        with self.__packetListenerLock:
            if listener not in self.__packetListeners:
                self.__packetListeners.append(listener)

    def removePacketListener(self, listener):
        with self.__packetListenerLock:
            if listener in self.__packetListeners:
                self.__packetListeners.remove(listener)

    def notifyPacketListeners(self, pkt):
        # Must leave link at same spot as when it was entered, swallow any MathLinkExceptions,
        #  and clear any MathLink error state.
        # Return false to indicate that processing by further packet
        #  listeners and default mechanisms should not take place.

        if len(self.__packetListeners) == 0:
            return True

        allowFurtherProcessing = True
        evt = PacketArrivedEvent(pkt, self)
        mark = 0
        try:
            mark = self._createMark()
        except:
            mark = 0
            self._clearError()
        else:
            for listener in self.__packetListeners:
                try:
                    try:
                        pkt_processor = listener.packetArrived
                    except:
                        pkt_processor = listener
                    allowFurtherProcessing = pkt_processor(evt)
                    if not allowFurtherProcessing:
                        break
                except MathLinkException as e:
                    self._clearError()
                finally:
                    self._seekMark(mark)
        finally:
            if mark != 0:
                self._destroyMark(mark)

        return allowFurtherProcessing

    @abstractmethod
    def _setUseNumPy(self, flag):
        raise NotImplemented

    def _get_put_array_params(self, ob):

        arr, t = self.Util.get_array_data_and_type(ob, self.use_numpy)
        print(arr)
        dims = self.Util.get_array_dims(ob, self.use_numpy)
        depth = len(dims)

        return arr, t, dims, depth

    def __next__(self):
        if self.ready:
            return self.get()
        else:
            raise StopIteration

    def __iter__(self):
        return self

    def drain(self):
        self.flush()
        return [ pkt for pkt in self ]

    def setLogging(self, val=True):
        self.Env.ALLOW_LOGGING = bool(val)