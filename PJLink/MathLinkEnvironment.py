"""The MathLinkFlags class is a single object that handles data type translation from flag ints

"""
from decimal import Decimal as decimal

##############################################################################################
#                                                                                            #
#                                  MathLinkEnvironment                                       #
#                                                                                            #
##############################################################################################

class MathLinkEnvironment:

    """A class holding all of the MathLink environment flags that will be used elsewhere in the package
    """

    ### These are all used by MathLink itself

    # The collection of packet type ints

    PACKET_TYPES = {
        "Illegal"    : 0,  # Constant returned by nextPacket
        "Call"       : 7,  # Constant returned by nextPacket.
        "Evaluate"   : 13,  # Constant returned by nextPacket.
        "Return"     : 3,  # Constant returned by nextPacket.
        "InputName"  : 8,  # Constant returned by nextPacket.
        "EnterText"  : 14,  # Constant returned by nextPacket.
        "EnterExpr"  : 15,  # Constant returned by nextPacket.
        "OutputName" : 9,  # Constant returned by nextPacket.
        "ReturnText" : 4,  # Constant returned by nextPacket.
        "ReturnExpr" : 16,  # Constant returned by nextPacket.
        "Display"    : 11,  # Constant returned by nextPacket.
        "DisplayEnd" : 12,  # Constant returned by nextPacket.
        "Message"    : 5,  # Constant returned by nextPacket.
        "Text"       : 2,  # Constant returned by nextPacket.
        "Input"      : 1,  # Constant returned by nextPacket.
        "InputString": 21,  # Constant returned by nextPacket.
        "Menu"       : 6,  # Constant returned by nextPacket.
        "Syntax"     : 10,  # Constant returned by nextPacket.
        "Suspend"    : 17,  # Constant returned by nextPacket.
        "Resume"     : 18,  # Constant returned by nextPacket.
        "BeginDialog": 19,  # Constant returned by nextPacket.
        "EndDialog"  : 20,
        "FirstUser"  : 128,
        "LastUser"   : 255,
        "FE"         : 100,  # Catch-all for packets that need to go to FE.
        "Expression" : 101  # Sent for Pr output
    }
    PACKET_TYPE_NAMES = {}
    PACKET_TYPE_NAMES.update(tuple((item, key) for key, item in PACKET_TYPES.items()))

    # The collection of message type ints

    MESSAGE_TYPES = {
        "Terminate"           : 1,
        "Interrupt"           : 2,
        "Abort"               : 3,
            # Used in putMessage() to cause the current Mathematica evaluation to be aborted.
        "AuthenticateFailure" : 10
          # Low-level message type that will be detected by a messagehandler function if the
          # kernel fails to start because of an authentication error (e.g., incorrect password file).
    }
    MESSAGE_TYPE_NAMES = {}
    MESSAGE_TYPE_NAMES.update(tuple((item, key) for key, item in MESSAGE_TYPES.items()))

    # The collection of type characters

    TYPE_TOKENS = {
        # Constants for use in putNext() or returned by getNext() and getType().
        "Function" : ord('F'),
        "String"   : ord('"'),
        "Symbol"   : ord('\043'),
        "Real"     : ord('*'),
        "Integer"  : ord('+'),
        "Error"    : 0,
        "Object"   : 100000
    }
    TYPE_TOKEN_NAMES = {}
    TYPE_TOKEN_NAMES.update(tuple((item, key) for key, item in TYPE_TOKENS.items()))

    # The collection of error type ints

    ERROR_TYPES = {
        # Some of these need to agree with C code.
        "Ok"                 : 0,
        "Memory"             : 8,
        "Unconnected"        : 10,
        "UnknownPacket"      : 23,
        "User"               : 1000,
        "NonMLError"         : 1000,
        "LinkIsNull"         : 1000,
        "OutOfMemory"        : 1001,
        "ArrayTooShallow"    : 1002,
        "BadComplex"         : 1003,
        "CreationFailed"     : 1004,
        "ConnectTimeout"     : 1005,
        "WrappedException"   : 1006,
        "BadObject"          : 1100,
        "FirstUserException" : 2000,
        "SignalCaught"       : 2100,
        "UnknownCallType"    : 2101
    }
    ERROR_TYPE_NAMES = {}
    ERROR_TYPE_NAMES.update(tuple((item, key) for key, item in ERROR_TYPES.items()))

    ERROR_MESSAGES = {
        "ArrayTooShallow" : "Array is not as deep as requested.",
        "BadComplex"      : "Expression could not be read as a complex number.",
        "ConnectTimeout"  : "The link was not connected before the requested time limit elapsed.",
        "BadObject"       : "Expression on link is not a valid Java object reference.",
        "FallThrough"     : "Extended error message not available.",
        "LinkIsNull"      : "Link is not open.",
        "CreationFailed"  : "Link failed to open.",
        "SignalCaught"    : "Signal was caught."
    }

    # These must remain in sync with Mathematica and C code. They don't really belong here,
    # but they are used in a few places, so it's convenient to dump them here.
    # If you change any of these, consult KernelLinkImpl, which has a few that
    # pick up where these leave off.

    MAX_ARRAY_DEPTH = 9
    TYPE_INTEGERS = {
        # Constants for use in getArray().
        "Boolean"    : -1,
        "Byte"       : -2,
        "Char"       : -3,
        "Short"      : -4,
        "Integer"    : -5,
        "Long"       : -6,
        "Float"      : -7,
        "Double"     : -8,
        "String"     : -9,
        "BigInteger" : -10,
        "Decimal"    : -11,
        "Expr"       : -12,
        "Complex"    : -13,
        ## exclusively for use in a KernelLink
        "Object"      : -14,
        "FloatOrInt"  : -15,
        "DoubleOrInt" : -16,
        "Array1D"     : -17,
        "Array2D"     : 2*(-17),#TYPE_ARRAY
        "Array3D"     : 3*(-17),#TYPE_ARRAY1
        "Array4D"     : 4*(-17),#TYPE_ARRAY1
        "Array5D"     : 5*(-17),#TYPE_ARRAY1
        "Array6D"     : 6*(-17),#TYPE_ARRAY1
        "Array7D"     : 7*(-17),#TYPE_ARRAY1
        "Array8D"     : 8*(-17),#TYPE_ARRAY1
        "Array9D"     : 9*(-17),#TYPE_ARRAY1
        "Bad"         : -10000
    }
    TYPE_INTEGER_NAMES = {}
    TYPE_INTEGER_NAMES.update(tuple((item, key) for key, item in TYPE_INTEGERS.items()))

    # "Complex" must always be the last one (largest absolute value number) of the set of types that have a byte value representation.
    # This rule does not apply to "Double"" or "Float", which are defined KernelLinkImpl and are not user-level constants.
    # They are never supplied as an argument to any J/Link method.

    ### Just for NumPy support

    try:
        import numpy
        HAS_NUMPY = True
    except ImportError:
        HAS_NUMPY = False

    ### For PIL support

    try:
        import PIL
        HAS_PIL = True
    except ImportError:
        HAS_PIL = False

    ### Maps for ease of type detection

    TYPE_MAP = {
        int     : "Long",
        float   : "Double",
        str     : "String",
        bool    : "Boolean",
        decimal : "Decimal",
        complex : "Complex"
    }
    TYPE_MAP.update(tuple((item, key) for key, item in TYPE_MAP.items()))
    if HAS_NUMPY:
        import numpy as np
        NUMPY_TYPE_MAP = {
            np.int64      : "Long",
            np.int32      : "Integer",
            np.int16      : "Short",
            np.int8       : "Char",
            np.float64    : "Double",
            np.float32    : "Float",
            np.complex128 : "Complex",
            np.complex64  : "Complex",
            np.bytes_     : "Byte",
            np.byte       : "Byte",
            np.str_       : "String",
            np.string_    : "String"
        }
        TYPE_MAP.update(NUMPY_TYPE_MAP.items())
        NUMPY_TYPE_MAP.update(tuple((item, key) for key, item in NUMPY_TYPE_MAP.items()))
    TYPE_MAP.update({
        "Integer"        : int,
        "Short"          : int,
        "BigInteger"     : int,
        "Float"          : float
    })

    TYPECODE_MAP = {
        'i' : "Integer",
        'h' : "Short",
        'l' : "Long",
        'f' : "Float",
        'd' : "Double",
        'b' : "Char",
        'B' : "Byte"
    }
    TYPECODE_MAP.update(tuple((item, key) for key, item in TYPECODE_MAP.items()))

    TYPENAME_MAP = {
        "byte"   : "Byte",
        "char"   : "Char",
        "short"  : "Short",
        "int"    : "Int",
        "long"   : "Long",
        "float"  : "Float",
        "double" : "Double",
        "bool"   : "Boolean",
        "bigint" : "BigInteger",
        "bigdec" : "Decimal",
        "complex": "Complex",
        "expr"   : "Expr"
    }

    CALL_TYPES = {
        "CallPython"       : 1,
        "LoadClass"        : 2, # Java legacy
        "Throw"            : 3,
        "ReleaseObject"    : 4,
        "Val"              : 5,
        "OnLoadClass"      : 6,
        "OnUnloadClass"    : 7,
        "SetComplex"       : 8,
        "Reflect"          : 9,
        "Show"             : 10,
        "SameQ"            : 11,
        "InstanceOf"       : 12,
        "AllowRagged"      : 13,
        "GetException"     : 14,
        "ConnectToFE"      : 15,
        "DisconnectToFE"   : 16,
        "PeekClasses"      : 17,
        "PeekObjects"      : 18,
        "ClassPath"        : 19,
        "AddToClassPath"   : 20,
        "SetUserID"        : 21,
        "AllowUIComputations" : 22,
        "UIThreadWaiting"  : 23,
        "YieldTime"        : 24,
        "GetConsole"       : 25,
        "ExtraLinks"       : 26,
        "GetWindowID"      : 27,
        "AddTitleChangeListener" : 28,
        "SetVMName"        : 29,
        "SetException"     : 30
    }
    CALL_TYPE_NAMES = {}
    CALL_TYPE_NAMES.update(tuple((item, key) for key, item in CALL_TYPES.items()))

    ### Types used by the Expr class
    EXPR_TYPES = {
        ### Expr flags

        'Unknown'          : 0,

        # Mathematica Expr types

        'Integer'          : 1,
        'Real'             : 2,
        'String'           : 3,
        'Symbol'           : 4,
        'Rational'         : 5,
        'Complex'	       : 6,

        # Python / Java types

        'BigInteger'       : 7, # Java legacy
        'BigDecimal'       : 8, # Java legacy
        'Decimal'          : 9, # python decimal.Decimal object

        # Composite types
        'FirstComposite'   : 100,
        'Function'         : 100,

        # Specialized arrays
        'FirstArrayType'   : 200,
        #'IntArray'        : 200, # I'm killing these because they don't really do anything in python
        #'REALARRAY1'      : 201,
        #'INTARRAY2'       : 202,
        #'REALARRAY2'      : 203,

        # Generalized list support
        'List'             : 208,

        # Association support
        'Association'      : 209,

        # efficient buffered data objects
        "Array"            : 214,
        'NumPyArray'       : 215,
        'BufferedNDArray'  : 216,

        # arbitrary object
        'Object'           : 999
    }
    EXPR_TYPE_NAMES = {}
    EXPR_TYPE_NAMES.update(tuple((item, key) for key, item in EXPR_TYPES.items()))

    ### Strings used by Expr I think? Or MathLink ?

    DECIMAL_POINT_STRING = '.'
    EXP_STRING = '*^'
    TICK_STRING = '`'

    ### Perfomance oriented flags

    # Used by _getArray and friends
    ALLOW_RAGGED_ARRAYS = False

    # Not currently used -- will force copies of data buffers to protect against corruption
    COPY_DATA_BUFFERS = False # I'm not sure I can actually disable this?

    CURRENT_MATHEMATICA = "11.3"

    if HAS_NUMPY:
        del np

    def __init__(self):
        raise TypeError("{} is a standalone class and cannot be instantiated".format(type(self).__name__))

    @staticmethod
    def __lookup(m, key, default=None):
        try:
            return m[key]
        except KeyError:
            return default

    @classmethod
    def toTypeInt(cls, o):
        """A convenience function that turns a python type, typcode, or type name into a type int

        :param o:
        :return:
        """

        tint = None
        try:
            tint = cls.TYPE_INTEGERS[o]
        except KeyError:
            for m in (cls.TYPE_MAP, cls.TYPECODE_MAP, cls.TYPE_INTEGERS, cls.TYPENAME_MAP):
                try:
                    tint = m[o]
                    if isinstance(tint, str):
                        tint = cls.TYPE_INTEGERS[tint]
                    break
                except KeyError:
                    pass

        return tint

    @classmethod
    def fromTypeInt(cls, tint, mode="intname"): ### THIS IS TERRIBLY DESIGNED TODO: MAKE IT NOT SUCK
        """A convenience function that turns a type int into a python type, typecode, or typename

        :param tint:
        :param mode: a string determining what to return, possible values are type, typecode, typename
        :return:
        """

        try:
            if isinstance(tint, int):
                tint = cls.TYPE_INTEGER_NAMES[tint]
            if mode == "typename":
                if tint in cls.TYPENAME_MAP:
                    otype = cls.TYPENAME_MAP[tint]
                elif isinstance(tint, str):
                    otype = tint
                else:
                    otype = None
            elif mode == "typecode":
                otype = cls.TYPECODE_MAP[tint]
            elif mode == "type":
                otype = cls.TYPE_MAP[tint]
            else:
                otype = cls.TYPENAME_MAP[tint]
        except KeyError:
            otype = None

        return otype

    @classmethod
    def getTypeNameFromTypeInt(cls, tint):
        return cls.__lookup(cls.TYPE_INTEGER_NAMES, tint)
    @classmethod
    def getTypeCodeFromTypeInt(cls, tint):
        if isinstance(tint, int):
            tint = cls.getTypeNameFromTypeInt(tint)
        return cls.__lookup(cls.TYPECODE_MAP, tint)
    @classmethod
    def getShortNameFromTypeInt(cls, tint):
        return cls.fromTypeInt(cls.TYPENAME_MAP, "typename")

    @classmethod
    def getObjectTypeInt(cls, ob):
        tint = None
        for t, n in cls.TYPE_MAP.items():
            if not isinstance(t, str) and isinstance(ob, t):
                tint = cls.TYPE_INTEGERS[n]

        return tint

    @classmethod
    def getObjectArrayTypeInt(cls, arr):
        """A convenience function that gets a type int for an iterable

        :param o:
        :return:
        """
        from array import array
        from .HelperClasses import BufferedNDArray

        tint = None
        if isinstance(arr, (bytes, bytearray)):
            tint = cls.toTypeInt("Byte")
        elif isinstance(arr, str):
            tint = cls.toTypeInt("Char")
        elif isinstance(arr, (BufferedNDArray, array)):
            tint = cls.toTypeInt(arr.typecode)

        if tint is None and cls.HAS_NUMPY:
            import numpy as np
            if isinstance(arr, np.ndarray):
                tint = cls.toTypeInt(arr.dtype.type)

        if tint is None:

            item = arr
            try:
                while True:
                    item2 = item[0]
                    if item2 is item:
                        break
                    else:
                        item = item2
            except:
                pass

            tint = cls.getObjectTypeInt(item)
        return tint

    @classmethod
    def fromTypeToken(cls, tchar):
        """A convenience function that turns a type char into a str

        :param tchar: (can be an int)
        :return:
        """

        try:
            if isinstance(tchar, str):
                tchar = ord(tchar)
            retstr = cls.TYPE_TOKEN_NAMES[tchar]
        except (KeyError, TypeError):
            retstr = None

        return retstr

    @classmethod
    def toTypeToken(cls, tstr):
        """A convenience function that turns a type char into a str

        :param tchar: (can be an int)
        :return:
        """

        try:
            tchar = cls.TYPE_TOKENS[tstr]
        except KeyError:
            tchar = None

        return tchar

    @classmethod
    def getNumPyTypeInt(cls, dtype):
        """A convenience function that turns a numpy.dtype a type int

        :param dtype:
        :return:
        """

        try:
            ttype = dtype.type
        except AttributeError:
            ttype = dtype

        return cls.toTypeInt(ttype)

    @classmethod
    def getNumPyType(cls, tint):
        """A convenience function that turns a numpy.dtype a type int

        :param dtype:
        :return:
        """

        try:
            ttype = cls.NUMPY_TYPE_MAP[tint]
        except KeyError:
            ttype = None

        return ttype

    @classmethod
    def allowRagged(cls):
        return cls.ALLOW_RAGGED_ARRAYS

    @classmethod
    def getExprTypeInt(cls, tstr):
        try:
            expint = cls.EXPR_TYPES[tstr]
        except KeyError:
            expint = None
        return expint
    @classmethod
    def getExprTypeName(cls, tint):
        try:
            expname = cls.EXPR_TYPE_NAMES[tint]
        except KeyError:
            expname = None
        return expname

    @classmethod
    def getErrorInt(cls, err_str):
        try:
            err_int = cls.ERROR_TYPES[err_str]
        except KeyError:
            err_int = None

        return err_int
    @classmethod
    def getErrorName(cls, err_no):
        try:
            err_name = cls.ERROR_TYPE_NAMES[err_no]
        except KeyError:
            err_name = None

        return err_name
    @classmethod
    def getErrorMessageText(cls, err_no, fallback = True):
        if isinstance(err_no, int):
            err_no = cls.getErrorName(err_no)

        msg = None
        try:
            msg = cls.ERROR_MESSAGES[err_no]
        except KeyError:
            if fallback:
              msg = cls.ERROR_MESSAGES["FallThrough"]

        return msg

    @classmethod
    def getPacketInt(cls, packet_name):
        try:
            packet_int = cls.PACKET_TYPES[packet_name]
        except KeyError:
            packet_int = None

        return packet_int
    @classmethod
    def getPacketName(cls, packet_int):
        try:
            packet_name = cls.PACKET_TYPE_NAMES[packet_int]
        except KeyError:
            packet_name = None

        return packet_name

    @classmethod
    def getMessageInt(cls, packet_name):
        try:
            packet_int = cls.MESSAGE_TYPES[packet_name]
        except KeyError:
            packet_int = None

        return packet_int
    @classmethod
    def getMessageName(cls, packet_int):
        try:
            packet_name = cls.MESSAGE_TYPE_NAMES[packet_int]
        except KeyError:
            packet_name = None

        return packet_name

    @classmethod
    def getCallInt(cls, packet_name):
        try:
            packet_int = cls.CALL_TYPES[packet_name]
        except KeyError:
            packet_int = None

        return packet_int
    @classmethod
    def getCallName(cls, packet_int):
        try:
            packet_name = cls.CALL_TYPE_NAMES[packet_int]
        except KeyError:
            packet_name = None

        return packet_name

    @classmethod
    def get_Mathematica_name(cls, version = None):
        import platform, os, re

        mname = version
        plat = platform.system()
        if plat == "Darwin":
            if mname is None:
                mname = "Mathematica.app"
            elif isinstance(mname, float) or (isinstance(mname, str) and re.match(r"\d\d.\d", mname)):
                mname = "Mathematica {}.app".format(mname)
        elif plat == "Linux":
            if mname is None:
                mname = os.path.join("Mathematica", cls.CURRENT_MATHEMATICA)
            elif isinstance(mname, float) or (isinstance(mname, str) and re.match(r"\d\d.\d", mname)):
                mname = os.path.join("Mathematica", str(mname))
        elif plat == "Windows":
            if mname is None:
                mname = os.path.join("Mathematica", cls.CURRENT_MATHEMATICA)
            elif isinstance(mname, float) or (isinstance(mname, str) and re.match(r"\d\d.\d", mname)):
                mname = os.path.join("Mathematica", str(mname))

        return mname

    @classmethod
    def get_Mathematica_root(cls, mname = None):
        import platform, os

        plat = platform.system()
        mname = cls.get_Mathematica_name(mname)
        if plat == "Darwin":
            root = os.sep + os.path.join("Applications", mname, "Contents")
        elif plat == "Linux":
            root = os.sep + os.path.join("usr", "local", "Wolfram", mname)
        elif plat == "Windows":
            root = os.path.expandvars(os.path.join("%ProgramFiles%", "Wolfram Research", mname))
        else:
            raise ValueError("Couldn't find Mathematica for platform {}".format(plat, bin))

        return root

    @classmethod
    def get_Mathematica_binary(cls, version = None):
        import platform, os

        plat = platform.system()

        try:
            root = cls.get_Mathematica_root(version)
        except ValueError:
            if not (isinstance(version, str) and os.path.isfile(version)):
                raise ValueError("Don't know how to find the WolframKernel executable on system {}".format(plat))

        if plat == "Darwin":
            bin = os.path.join(root, "MacOS", "WolframKernel")
        elif plat == "Linux":
            bin = os.path.join(root, "SystemFiles", "Kernel", "Binaries", "Linux-x86-64", "WolframKernel")
        elif plat == "Windows":
            bin = os.path.join(root, "wolfram")

        if not os.path.isfile(bin):
            raise ValueError("Couldn't find binary for platform {} ({} is not a file)".format(plat, bin))

        return bin

    @classmethod
    def get_MathLink_library(cls, version = None):
        import platform, os

        plat = platform.system()
        try:
            root = cls.get_Mathematica_root(version)
        except ValueError:
            if not (isinstance(version, str) and os.path.isfile(version)):
                raise ValueError("Don't know how to MathLink library on system {}".format(plat))

        lib = os.path.join(root, "SystemFiles", "Links", "MathLink", "DeveloperKit", )

        if not os.path.isfile(bin):
            raise ValueError("Couldn't find binary for platform {} ({} is not a file)".format(plat, bin))

        return bin