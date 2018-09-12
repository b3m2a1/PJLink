"""Helper classes used through PJLink to facilitate MathLink communication

"""

from .MathLinkEnvironment import MathLinkEnvironment as Env
from .MathLinkExceptions import MathLinkException

###############################################################################################
#                                                                                             #
#                                       NamedTuple Types                                      #
#                                                                                             #
###############################################################################################

from collections import namedtuple

#                                            MLFunction                                       #
MLFunction         = namedtuple("MLFunction",         ["head", "argCount"])

#                                            MLExpr                                           #
MLExpr             = namedtuple("MLExpr",             ["head", "args", "end"])
MLExpr.__new__.__defaults__ = (False,)
def expr_repr(expr):
    return "{}[{}]".format(expr.head, ", ".join(repr(x) for x in expr.args))
expr_repr.name = "__repr__"
MLExpr.__repr__ = expr_repr
del expr_repr

#                                            MLSym                                            #
MLSym              = namedtuple("MLSym",              ["name"]            )
def sym_repr(sym):
    return "{}".format(sym.name)
sym_repr.name = "__repr__"
MLSym.__repr__ =sym_repr
del sym_repr

#                                            MLUnevaluated                                    #
MLUnevaluated      = namedtuple("MLUnevaluated",      ["arg"]             )
def uneval_repr(uneval):
    return "{}".format(uneval.arg)
uneval_repr.name = "__repr__"
MLUnevaluated.__repr__ = uneval_repr
del uneval_repr

#                                            PacketArrivedEvent                               #
PacketArrivedEvent = namedtuple("PacketArrivedEvent", ["packet", "link"]  )

#                                            MsgHandlerRecord                                 #
MsgHandlerRecord   = namedtuple("MsgHandlerRecord",   ["method", "target"])

###############################################################################################
#                                                                                             #
#                                       BufferedNDArray                                       #
#                                                                                             #
###############################################################################################

class BufferedNDArray:
    """BufferedNDArray is a hack class for data transfer when NumPy is not an option

It doesn't do anything fancy -- it's just stitches together a single buffered array to pass / return
Once initialized the array expects to not change its size so watch out for that
Some slicing capability is added for giggles
    """
    def __init__(self, buff, dims, offsets = (0, 0)):
        self._buffer = buff
        self.__shape = tuple(dims)
        self.__offsets = tuple(offsets)

    @classmethod
    def from_buffers(cls, buffs, dims):
        bob = None
        for b in buffs:
            if bob is None:
                bob = cls(b, dims)
            else:
                bob.extend(b)
        bob.adjust()
        return bob

    @staticmethod
    def __prod(iterable):
        from functools import reduce
        from operator import mul
        return reduce(mul, iterable, 1)

    @property
    def valid(self):
        try:
            self.adjust()
            return True
        except ValueError:
            return False

    def adjust(self):
        start, end = self.__offsets
        elems = start + self.__prod(self.__shape)
        end = len(self._buffer) - elems
        if 0 > end:
            raise ValueError("Buffer dimension exceeds buffer size")
        else:
            self.__offsets = (start, end)
    @property
    def shape(self):
        return tuple(self.__shape)
    @shape.setter
    def shape(self, new):
        new = tuple(new)
        old = self.__shape
        try:
            self.__shape = new
            self.adjust()
        except ValueError:
            self.__shape = old
            raise ValueError("New dimension would exceed buffer size")

    @property
    def offsets(self):
        return tuple(self.__offsets)
    @offsets.setter
    def offsets(self, new):
        if len(new) == 2:
            new = tuple(new)
            elems = new[0] + self.__prod(self.__shape)
            if elems != len(self._buffer) - new[1]:
                raise ValueError("New offsets don't match buffer size")
            else:
                self.__offsets=new
        else:
            raise ValueError("offsets must be of length 2")

    @property
    def size(self):
        return len(self._buffer) - self.__offsets[1] - self.__offsets[0]

    def __len__(self):
        return len(self.__shape)

    @property
    def typecode(self):
        return self._buffer.typecode

    def extend(self, ob):
        self._buffer.extend(ob)

    def slide(self, q):
        self.offsets = [x + q*z for x, z in zip(self.__offsets, (1, -1)) ]

    def tonumpy(self):
        import numpy as np
        arr = np.array(self._buffer[self.__offsets[0]:len(self._buffer)-self.__offsets[1]])
        return arr.reshape(self.__shape)

    def __calculate_slice_coordinates(self, coords):
        import itertools

        shape = self.__shape
        if len(coords) > len(shape):
            raise IndexError('{}: requested depth {} is greater than actual depth {}'.format(type(self).__name__, len(coords), len(shape)))

        part_prods = [ self.__prod(shape[i:]) for i in range(1, len(shape)) ]
        part_prods.append(1)
        start, end = self.__offsets
        fdim = list(shape)

        i=0
        shift = part_prods[0] if len(part_prods) > 0 else 0
        for ind, num, s, i in zip(coords, part_prods, shape, range(len(shape))):
            if isinstance(ind, int):
                if ind<0:
                    ind += s
                if isinstance(start ,int):
                    start += ind*num
                else:
                    start = [s + ind*num for s in start]
                fdim[i] = 0

            elif isinstance(ind, slice):
                i_crds = range(s)[ind]
                fdim[i] = len(i_crds)
                if isinstance(start, int):
                    start = [ start+i*num for i in i_crds ]
                else:
                    start = list(itertools.chain.from_iterable([ s+i*num for s in start ] for i in i_crds))

        fdim = tuple( x for x in fdim if x > 0 )

        return start, num, fdim, len(shape) - i

    def __get_slice(self, start, shift, newdim, dims):
        if dims == 0:
            return self._buffer[start]
        elif dims == 1 and isinstance(start, int):
            return self._buffer[start:start + shift]
        elif isinstance(start, int):
            bob = type(self)(self._buffer, newdim, offsets = (start, len(self._buffer) - (start + shift)))
            return bob
        else:
            if len(start) == 1 and shift == 0:
                new_buf = self._buffer[:1]
                new_buf[0] = self._buffer[start[0]]
            elif shift == 0:
                stop = start[-1]
                step = start[1] - start[0]
                tart = start[0]
                new_buf = self._buffer[tart:stop:step]
            else:
                new_buf = self._buffer[:shift*len(start)]
                for i, s in enumerate(start):
                    new_buf[i*shift:(i+1)*shift] = self._buffer[s:s+shift]
            bob = type(self)(new_buf, newdim, offsets = (0, 0))
            return bob

    def __set_slice(self, value, start, shift, newdim, dims):
        import array, itertools

        if dims == 0:
            if len(value) != 0:
                raise ValueError("{}: expected object of length {} got object of length {}".format(type(self).__name__, 0, len(value)))
            self._buffer[start] = value
        elif dims == 1 and isinstance(start, int):
            if len(value) != shift:
                raise ValueError("{}: expected object of length {} got object of length {}".format(type(self).__name__, shift, len(value)))
            self._buffer[start:start + shift] = array.array(self.typecode, value)
        elif isinstance(start, int):
            try:
                while True:
                    iter(value[0]) # test
                    value = list(itertools.chain.from_iterable(value))
            except:
                pass
            if len(value) != shift:
                raise ValueError("{}: expected object of with total number of elements {} got {}".format(type(self).__name__, shift, len(value)))
            self._buffer[start:start + shift] = array.array(self.typecode, value)
        else:
            if len(start) == 1 and shift == 0:
                self._buffer[start] = value[0]
            elif shift == 0:
                stop = start[-1]
                step = start[1] - start[0]
                tart = start[0]
                diff = max(tart, stop) - min(tart, stop)
                test_len = len(range(diff)[tart:stop:step])
                if len(value) != test_len:
                    raise ValueError("{}: expected object of length {} got object of length {}".format(type(self).__name__, test_len, len(value)))
                self._buffer[tart:stop:step] = value
            else:
                try:
                    while True:
                        iter(value[0][0]) # test
                        value = list(itertools.chain.from_iterable(value))
                except:
                    pass
                try:
                    iter(value[0])
                except:
                    raise ValueError("{}: need slices (iterables) at deepest level but got non-iterable of type {}".format(type(self).__name__, type(value[0]).__name__))
                if len(value) != len(start):
                    raise ValueError("{}: need {} slices at deepest level but got {}".format(type(self).__name__, len(start), len(value)))
                for i, zz in enumerate(zip(start, value)):
                    s, v = zz
                    if len(v) != shift:
                        raise ValueError("{}: expected object where the number of elements at the deepest level is {} got {}".format(type(self).__name__, shift, len(v)))
                    self._buffer[s:s+shift] = array.array(self.typecode, v)

    def __getitem__(self, ind):
        self.adjust()
        if isinstance(ind, (int, slice)):
            coords = self.__calculate_slice_coordinates([ind])
            return self.__get_slice(*coords)
        elif all((isinstance(item, (int, slice)) for item in ind)):
            coords = self.__calculate_slice_coordinates(ind)
            return self.__get_slice(*coords)
        elif len(ind) > 0:
            raise TypeError("{} indices must be integers or slices or tuples of ints, not {}".format(type(self).__name__, type(slice[0]).__name__))
        else:
            raise TypeError("{} indices must be integers or slices or tuples of ints, not {}".format(type(self).__name__, type(slice).__name__))

    def __setitem__(self, ind, value):
        self.adjust()
        if isinstance(ind, (int, slice)):
            coords = self.__calculate_slice_coordinates([ind])
            return self.__set_slice(value, *coords)
        elif all((isinstance(item, (int, slice)) for item in ind)):
            coords = self.__calculate_slice_coordinates(ind)
            return self.__set_slice(value, *coords)
        elif len(ind) > 0:
            raise TypeError("{} indices must be integers or slices or tuples of ints, not {}".format(type(self).__name__, type(slice[0]).__name__))
        else:
            raise TypeError("{} indices must be integers or slices or tuples of ints, not {}".format(type(self).__name__, type(slice).__name__))



    def __eq__(self, other):
        return isinstance(other, type(self)) and self.shape == other.shape and self.offsets == other.offsets and self._buffer == other._buffer

    def __repr__(self):
        return "{}(typecode='{}', shape={}, size={})".format(type(self).__name__, self.typecode, self.shape, self.size)

###############################################################################################
#                                                                                             #
#                                         LinkWrapper                                         #
#                                                                                             #
###############################################################################################

class LinkWrapper:
    """A wrapper to allow with ...: syntax on a link

    """
    def __init__(self, parent, checkLink = True, checkError = True, check = None, lock = True):
        self.parent = parent
        self.check = check
        self.checkLink = checkLink
        self.checkError = checkError
        self.lock = lock

        self.__locked = False
    def __enter__(self):
        if self.checkLink:
            self.parent._check_link()
        if self.lock:
            self.__locked = True
            self.parent.thread_lock.acquire()
    def __exit__(self, type, value, traceback):
        if self.__locked:
            self.parent.thread_lock.release()
        if self.checkError:
            self.parent._check_error(self.check)

###############################################################################################
#                                                                                             #
#                                         ArrayUtils                                          #
#                                                                                             #
###############################################################################################

class ArrayUtils:
    """ArrayUtils is a standalone class that supports basic, shared array options.
This includes things like getting array dimensions, casts to BufferedNDArray, type extraction, etc.

    """

    def __init__(self):
        raise TypeError("{} is a standalone class and can not be instantiated".format(type(self).__name__))

    @staticmethod
    def zeros(dims):
        # this is an ugly, gross, dangerous hack but also only like two lines of code...
        # could also do via http://code.activestate.com/recipes/577061-nest-a-flat-list/
        # all methods will be slow, unfortunately... (hence BufferedNDArray)

        meta = '0'
        for i, n in enumerate(dims):
            meta = "[ {} for i_{} in range({}) ]".format(meta, i, n)
        return eval(meta)

    @staticmethod
    def get_array_object(array_type, item):
        import array

        test_array_type_int = Env.getObjectArrayTypeInt(item)
        test_array_type = Env.fromTypeInt(test_array_type_int, "typecode")
        if test_array_type is None:
            test_array_type = test_array_type_int
        if array_type is not None and test_array_type != array_type:
            raise TypeError("MathLink can only handle homogenous type data")

        if isinstance(test_array_type, int):
            res = item
        elif isinstance(test_array_type, str):
            try:
                res = array.array(test_array_type, item)
            except ValueError:
                raise TypeError("MathLink can only handle homogenous type data")
        else:
            raise TypeError("MathLink can't handle data of type {}".format(item[0]))

        return test_array_type, res

    @classmethod
    def get_array_data_and_type(cls, ob, use_numpy):
        res = None
        if use_numpy:
            import numpy as np
            if isinstance(ob, np.ndarray):
                res = ob
            elif isinstance(ob, BufferedNDArray):
                res = ob.tonumpy()
            else:
                res = np.array(ob)
            array_type = Env.getNumPyTypeInt(res.dtype.type)
        elif isinstance(ob, BufferedNDArray):
            res = ob
            array_type = Env.toTypeInt(ob.typecode)
        else:
            import array, itertools
            dims = cls.get_array_dims(ob, use_numpy)
            if 0 in dims:
                raise ValueError("PJLink currently can't handle length 0 arrays")

            array_type = None
            res = None

            index_iter = itertools.product(*(range(n) for n in dims[:-1]))
            index = next(index_iter)

            item = ob
            for i in index:
                item = item[i]

            item_arr, array_type = cls.get_array_data_and_type(item, array_type)

            if isinstance(item_arr, array.array):
                res = BufferedNDArray(item_arr, dims)
            else:
                res = cls.zeros(dims)
                rl = res
                for i in index:
                    if rl[i] is not None:
                        rl = rl[i]

            for index in itertools.product(*(range(n) for n in dims[:-1])):
                # maybe I could do this more efficiently by not reindexing, but I don't
                # know how to get this kind of metaprogramming working well here

                item = ob
                if isinstance(res, BufferedNDArray):
                    for i in index:
                        item = item[i]
                else:
                    rl = res
                    for i in index:
                        if rl[i] is not None:
                            rl = rl[i]
                        item = item[i]

                item_arr, array_type = cls.get_array_object(item, array_type)

                if isinstance(res, BufferedNDArray):
                    res.extend(item_arr)
                else:
                    rl[i]=item_arr

            if isinstance(array_type, str):
                array_type = Env.toTypeInt(array_type)

        return res, array_type

    @classmethod
    def get_array_dims(cls, ob, use_numpy):

        if use_numpy:
            arr, t = cls.get_array_data_and_type(ob, use_numpy)
            dims = arr.shape
        elif isinstance(ob, BufferedNDArray):
            dims = ob.shape
        else:
            depth = cls.get_array_depth(ob, use_numpy)
            dims = [ None ] * depth
            do = ob
            for i in range(depth):
                try:
                    dims[i] = len(do)
                except TypeError:
                    dims[i] = 0
                    break
                else:
                    do = do[0]

        return dims

    @classmethod
    def get_array_depth(cls, ob, use_numpy):

        if use_numpy:
            arr, t = cls.get_array_data_and_type(ob, use_numpy)
            depth = len(arr.shape)
        else:
            depth = 1
            do = ob
            try:
                while hasattr(do, "__getitem__"):
                    do = do[0] # a good further test that it's indexable
                    depth += 1
            except:
                pass

        return depth



###############################################################################################
#                                                                                             #
#                                        MExprUtils                                           #
#                                                                                             #
###############################################################################################

class MExprUtils:
    """A set of quick little utilities for working with MExprs. Attempts to be a partial replacement
for the JLink package on the Mathematica side
    """

    PackageContext = "PJLink`"
    PackagePrivate = PackageContext+"`Private`"
    PackagePackage = PackageContext+"`Package`"

    def __init__(self):
        raise NotImplemented

    @classmethod
    def _sym(cls, sym):
        return MLSym(cls.PackageContext+sym)
    @classmethod
    def _psym(cls, sym):
        return MLSym(cls.PackagePackage+sym)
    @classmethod
    def _prsym(cls, sym):
        return MLSym(cls.PackagePrivate+sym)

    @classmethod
    def _rules(cls, kwargs):
        """Unwraps a dict or OrderedDict into a sequence of Rule or RuleDelayed

        :param kwargs:
        :return:
        """
        opts = [ None ] * len(kwargs)
        for i, pair in enumerate(kwargs.items()):
            key, val = pair
            if val is not None:
                if key.endswith("_"):
                    key = MLSym(key.strip("_"))
                rhead = "Rule"
                if isinstance(val, MLUnevaluated):
                    val = MLUnevaluated.arg
                    rhead = "RuleDelayed"
                opts[i] = MLExpr(rhead, (key, val))
        opts = [ o for o in opts if o is not None ]
        return opts
    @classmethod
    def _varlist(cls, defs):
        """Creates an assignment list for things like Block and Module

        :param defs:
        :return:
        """
        from collections import OrderedDict

        if not isinstance(defs, (dict, OrderedDict)):
            opts = [ MLSym(d) if isinstance(d, str) else d for d in defs ]
        else:
            opts = [ None ] * len(defs)
            for i, pair in enumerate(defs.items()):
                key, val = pair
                key = MLSym(key)
                if val is None:
                    opts[i] = key
                else:
                    rhead = "Set"
                    if isinstance(val, MLUnevaluated):
                        val = MLUnevaluated.arg
                        rhead = "SetDelayed"
                    opts[i] = MLExpr(rhead, (key, val))
        return opts
    @classmethod
    def _function(cls, head, *args, **kwargs):
        """Unwraps into a function call

        :param head:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            end = kwargs["_EndPacket"]
            del kwargs["_EndPacket"]
        except KeyError:
            end = False
        args = args + tuple(cls._rules(kwargs))
        return MLExpr(head, args, end = end)
    F = _function #to make life nicer since this will likely be used so often

    @classmethod
    def Set(cls, lhs, rhs):
        return MLExpr("Set", lhs, rhs)
    @classmethod
    def SetDelayed(cls, lhs, rhs):
        return MLExpr("SetDelayed", lhs, rhs)
    s  = Set
    sd = SetDelayed
    @classmethod
    def Unset(cls, lhs, rhs):
        return MLExpr("Unset", lhs, rhs)
    u = Unset

    @classmethod
    def List(cls, *args):
        return MLExpr("List", args)
    @classmethod
    def Rule(cls, key, val):
        return MLExpr("Rule", (key, val))
    @classmethod
    def RuleDelayed(cls, key, val):
        return MLExpr("RuleDelayed", (key, val))

    @classmethod
    def _localized_method(cls, head, defs, *body, **opts):
        return cls.F(
            head,
            cls._varlist(defs),
            cls.do(*body),
            **opts
        )
    @classmethod
    def Block(cls, defs, *body):
        return cls._localized_method("Block", defs, *body)
    @classmethod
    def Module(cls, defs, *body):
        return cls._localized_method("Module", defs, *body)
    @classmethod
    def With(cls, defs, *body):
        return cls._localized_method("With", defs, *body)

    @classmethod
    def CompoundExpression(cls, *args):
        return MLExpr("CompoundExpression", args)
    do = CompoundExpression

    @classmethod
    def _blank_func(cls, head, body=None):
        if isinstance(body, str):
            body = MLSym(body)
        if isinstance(body, MLSym):
            arg = cls.F(head, body)
        else:
            arg = cls.F(head)
        return arg
    @classmethod
    def Blank(cls, body=None):
        return cls._blank_func("Blank", body)
    @classmethod
    def BlankSequence(cls, body=None):
        return cls._blank_func("BlankSequence", body)
    @classmethod
    def BlankSequenceNull(cls, body=None):
        return cls._blank_func("BlankSequenceNull", body)

    @classmethod
    def setup_teardown(cls, setup, expr, teardown):
        return cls.F(
            "Internal`WithLocalSettings",
            setup, expr, teardown
        )
    @classmethod
    def new_context_path(cls, cpath):
        return cls.F(
            "System`Private`NewContextPath",
            cls.List(cpath)
            )
    @classmethod
    def restore_context_path(cls):
        return cls.F("System`Private`RestoreContextPath")
    @classmethod
    def with_context(cls, context, cpath, expr):
        setup = [
            cls.s(cls._psym("cachedContext"), MLSym("$Context"))
        ]
        teardown = [
            cls.s(MLSym("$Context"), cls._psym("cachedContext"))
        ]
        if context is not None:
            setup.append(cls.s(MLSym("$Context"), context))
            teardown.append(cls.s(MLSym("$Context"), context))
        if cpath is not None:
            setup.append(cls.new_context_path(cpath))
            teardown.append(cls.restore_context_path())

        return cls.setup_teardown(
            cls.do(*setup),
            expr,
            cls.do(*teardown)
        )

    @classmethod
    def register_symbol(cls, name):
        import re
        sym_re    = "([^\W\d_])+"
        sym_re    = re.compile(sym_re, re.U)
        if re.match(sym_re, name):
            setattr(cls, name, MLSym(name))

    @classmethod
    def register_function(cls, fname, *argnames, **kwargs):
        """This registers the Mathematica function fname to be called more cleanly.

        One major caveat is that the arguments are always *args and **kwargs (varargs and varkwargs)
        :param fname:
        :return:
        """
        import re

        sym_re    = "([^\W\d_])+"
        sym_re    = re.compile(sym_re, re.U)
        anames    = [ a for a in argnames if not a.endswith("___") and re.match(sym_re, a) ]
        kwvals    = [ (k, val) for k, val in kwargs.items() if not k == "OptionsPattern" and re.match(sym_re, k.strip("_")) ]
        varargs   = len(argnames) > 0 and argnames[-1].endswith('___')
        varkwargs = "OptionsPattern" in kwargs and kwargs["OptionsPattern"]

        ### time to play with fire...
        argstr  = ", ".join(anames)
        callstr = ", ".join(anames)
        if varargs:
            varargsname = argnames[-1].strip("___")
            if varargsname == "":
                varargsname = "args"
            if varargsname in anames:
                varargsname = "ArgBlankNullSequence"
            if len(argstr)>0:
                argstr  += ", "
                callstr += ", "
            argstr  += "*"+varargsname
            callstr += "*"+varargsname
        for k, v in kwvals:
            if len(argstr)>0:
                argstr  += ", "
                callstr += ", "
            argstr  += "{}={}".format(k.strip("_"), "'"+v+"'" if isinstance(v, str) else v)
            callstr += "{}={}".format(k, k.strip("_"))
        if len(argstr)>0:
            argstr  += ", "
            callstr += ", "
        argstr +="_EndPacket=False"
        callstr+="_EndPacket=_EndPacket"
        if varkwargs:
            if "OptionsPattern" in anames or "OptionsPattern" in kwvals:
                varargsname = "OptionsPatternDict"
            else:
                varargsname = "OptionsPattern"
            if len(argstr)>0:
                argstr  += ", "
                callstr += ", "
            argstr  += "**"+varargsname
            callstr += "**"+varargsname

        if len(argstr)>0:
            argstr  = ", " + argstr
            callstr = ", " + callstr

        #dunno a better way to hack this in...
        meta = '''@classmethod
def template_classmethod(clas{}):
    return clas.F('{}'{})
        '''.format(argstr, fname, callstr)

        meth_def = compile(meta, "<{}:method_register>".format(cls.__name__), 'exec')
        env = {}
        exec(meth_def, globals(), env)
        template_classmethod = env["template_classmethod"] # unfortunate hack based on a python opt
        if template_classmethod is not None:
            template_classmethod.__name__ = fname
            setattr(cls, fname, template_classmethod)

MExprUtils.register_function("Needs", "pkg", "file___")
MExprUtils.register_function("Get", "pkg")
MExprUtils.register_function("Import", "file", "fmt___", OptionsPattern=True)
MExprUtils.register_function("Export", "file", "expr", "fmt___", OptionsPattern=True)
MExprUtils.register_function("ExportString", "expr", "fmt___", OptionsPattern=True)

MExprUtils.register_symbol("True")
MExprUtils.register_symbol("False")
MExprUtils.register_symbol("Null")
MExprUtils.register_symbol("Automatic")

MExprUtils.register_function("Switch", "type", "pat1", "body1", "patBodies___")
MExprUtils.register_function("If", "test", "true", "false", "indet___")
MExprUtils.register_function("Greater", "a", "b")
MExprUtils.register_function("Less", "a", "b")
MExprUtils.register_function("Less", "a", "b")

MExprUtils.register_function("Names", 'pat', IgnoreCase_=None, SpellingCorrection_=None)
MExprUtils.register_function("ToString", 'expr', FormatType_=None, PageWidth_=None, OptionsPattern=True)
MExprUtils.register_function("ToBoxes", 'expr', "fmt___")
MExprUtils.register_function("ToExpression", 'str', "fmtHead___")
MExprUtils.register_function("FrontEndExecute", 'expr')
MExprUtils.register_function("UsingFrontEnd", 'expr')
MExprUtils.register_function("SystemOpen")

for pkt in (
    "Illegal", "Call", "Evaluate",
    "Return", "InputName", "EnterText",
    "EnterExpression", "OutputName", "ReturnText",
    "ReturnExpression", "Display", "DisplayEnd",
    "Message", "Text", "Input", "InputString", "Menu",
    "Syntax", "Suspend", "Resume", "BeginDialog", "EndDialog",
    "Expression"
    ):
    MExprUtils.register_function(pkt+"Packet", "expr___")


###############################################################################################
#                                                                                             #
#                                        MPackage                                             #
#                                                                                             #
###############################################################################################

class MPackage(MExprUtils):
    """MPackage is a class that holds high-level package functions lifted from JLink for use in PJLink

    """

    JLinkContext           = "JLink"
    JLinkEvaluateToContext = JLinkContext + "`EvaluateTo`"

    @classmethod
    def _eval(cls, expr):
        return cls.EvaluatePacket(expr, _EndPacket=True)

    @classmethod
    def __get_evaluate_to_parameters(cls, obj, page_width, format):
        import math

        if page_width is None:
            page_width = 0
        elif page_width is math.inf:
            page_width = MLSym("Infinity")
        elif not isinstance(page_width, int):
            raise TypeError("PageWidth {} should be an integer".format(page_width))
        elif page_width <= 0:
            page_width = MLSym("Infinity")

        if format is None:
            format = "InputForm"
        elif isinstance(format, MLSym):
            format = MLSym.name
        if not isinstance(format, str):
            raise TypeError("Format type should be a string instead of {}".format(format))

        return cls.ToExpression(obj) if isinstance(obj, str) else obj, page_width, MLSym(format)

    @classmethod
    def _load_JLink_packet(cls):
        return cls._eval(cls.Needs(cls.JLinkContext))

    @classmethod
    def _to_cell_expr(cls, obj, page_width = None, format = None, **kw):
        """Python rep of:
            Block[
                {$DisplayFunction = Identity, expr, pWidth},
                expr = If[StringQ[Unevaluated @ e], ToExpression @ e, e];
                pWidth = If[Greater[pageWidth, 0], pageWidth, Infinity];
                Switch[
                    expr, _Cell,
                        expr, _BoxData,
                        Cell[expr,
                            "Output", ShowCellBracket -> False, CellMargins -> {{0, 0}, {0, 0}},
                            PageWidth -> pWidth, cellOpts
                        ],
                    _,
                        Cell[BoxData @ ToBoxes[expr, frm],
                            "Output", ShowCellBracket -> False, CellMargins -> {{0, 0}, {0, 0}},
                            PageWidth -> pWidth, cellOpts
                        ]
                ]
            ];
        """
        obj, page_width, format = cls.__get_evaluate_to_parameters(obj, page_width, format)
        expr = MLSym("expr")
        kw.update(ShowCellBracket_=False, CellMargins_=[[0, 0], [0, 0]], PageWidth_=page_width)
        return cls.Block(
            {
                "$DisplayFunction_" : MLSym("Identity"),
                "expr"   : None
            },
            cls.Set(expr, obj),
            cls.Switch(expr,
                cls.Blank("Cell"),    expr,
                cls.Blank("BoxData"), cls.F("Cell", expr, "Output", *kw),
                cls.Blank(),          cls.F("Cell", cls.ToBoxes(expr, format), "Output", *kw)
                )
        )

    @classmethod
    def _front_end_shared_q(cls):
        return cls.F("SameQ", cls.F("Head", MLSym("MathLink`ServiceLink")), MLSym("LinkObject"))

    @classmethod
    def _eval_to_string(cls, obj, page_width=None, format=None, **ops):
        obj, page_width, format = cls.__get_evaluate_to_parameters(obj, page_width, format)
        return cls.ToString(obj, FormatType = format, PageWidth = page_width, **ops)
    @classmethod
    def _eval_to_typset_string(cls, obj, page_width = None, format = None, export_format = None, **kw):
        """Python rep of:
             Block[
                {cellExpr, result},
                cellExpr = JLink`ConvertToCellExpression[e, frm, pageWidth, opts];
                ExportString[cellExpr, format]
              ];
        """

        expr_packet = cls._to_cell_expr(obj, page_width, format, **kw)
        expr = MLSym("cellExpr")
        if export_format is None:
            export_format = "GIF"
        return cls.with_context(
            cls.PackagePrivate,
            [ cls.PackagePrivate, "System`" ],
            cls.Block(
                [ "cellExpr", "res" ],
                cls.Set(expr, expr_packet),
                cls.Set(MLSym("res"), cls.F("ExportString", expr, export_format, **kw))
                )
            )
    @classmethod
    def _eval_to_image_string(cls, obj, export_format = None, **kw):
        """Python rep of:
             ExportString[cellExpr, format, ops]
        """

        if export_format is None:
            export_format = "GIF"
        return cls.F("ExportString", obj, export_format, **kw)
    @classmethod
    def _eval_to_image_data(cls, obj, **kw):
        return cls.F("ImageData", cls.F("Rasterize", obj, **kw))

    @classmethod
    def _eval_to_string_packet(cls, obj, page_width=None, format=None, **ops):
        return cls._eval(cls._eval_to_string(obj, page_width=page_width, format=format, **ops))
    @classmethod
    def _eval_to_typeset_packet(cls, obj, page_width=None, format=None, export_format=None, **ops):
        return cls._eval(cls._eval_to_typset_string(obj, page_width=page_width, format=format, export_format = None, **ops))
    @classmethod
    def _eval_to_image_packet(cls, obj, export_format=None, **ops):
        return cls._eval(cls._eval_to_image_string(obj, export_format = None, **ops))

###############################################################################################
#                                                                                             #
#                                      ObjectHandler                                          #
#                                                                                             #
###############################################################################################
class ObjectHandler:
    """The utility of this is up for grabs in a dynamic language like python

    """

    class Context:
        """A kludge for object lookup

        """

        __context_cache = {}
        __in_constructor = False

        def __init__(self, name, envid):
            if not self.__in_constructor:
                raise NotImplemented
            self.__env   = envid
            self.__name  = name
            self.__names = {}

        @property
        def name(self):
            return self.__name

        def __getattr__(self, item):
            try:
                return self.__names[item]
            except KeyError:
                if item.endswith("__Context__"):
                    return self.get_subcontext(item[:-(len("__Context__")+1)])
                else:
                    raise NameError("Symbol '{}{}' not found".format(self.name, item))

        def __setattr__(self, key, value):
            if key.endswith("__Context__"):
                raise ValueError("Cannot assign to context {}".format(self.get_subcontext(key).name))
            self.__names[key] = value

        def get_subcontext(self, subpat):
            name = self.name+"`"+subpat+"`"
            try:
                cont = self.__context_cache[name]
            except KeyError:
                self.__in_constructor = True
                cont = type(self)(name)
                self.__in_constructor = False
                self.__context_cache[name] = cont
            return cont

        @classmethod
        def from_string(cls, full_name, env):
            try:
                cache = cls.__context_cache[id(env)]
            except KeyError:
                cache = {}
                cls.__context_cache[id(env)] = cache
            try:
                cont = cache[full_name]
            except KeyError:
                bits = full_name.split("`")
                cont = cls.from_parts(bits[:-2], env)
            return cont

        @classmethod
        def from_parts(cls, bits, env):
            try:
                cache = cls.__context_cache[id(env)]
            except KeyError:
                cache = {}
                cls.__context_cache[id(env)] = cache

            if len(bits) == 0:
                raise ValueError("Empty context")
            full_name = "`".join(bits)
            try:
                cont = cache[full_name]
            except KeyError:
                try:
                    cont = cache[bits[0]+"`"]
                except KeyError:
                    cls.__in_constructor = True
                    cont = cls(bits[0]+"`")
                    cls.__in_constructor = False

                for b in bits[1:]:
                    cont = cont.get_subcontext(b)

            return cont

    def __init__(self):
        raise NotImplemented

    @staticmethod
    def clean_symbol_names(name):
        name = name.replace("$", "_")
        name = name.replace("`", "__Context__.")
        return name

    @classmethod
    def get_object(cls, name, env):
        obj = None
        bits = name.split("`")
        if len(bits)>1:
            cont = cls.Context.from_string(bits[0]+"`", env)
            env[bits[0]+"__Context__"] = cont
        name = cls.clean_symbol_names(name)
        if name != "Null":
            obj = eval(name, env, env)
        return obj

    @classmethod
    def set_object(cls, name, val, env):
        bits = name.split("`")
        if len(bits)>1:
            # set the head context if necessary
            cont = cls.Context.from_string(bits[0]+"`", env)
            env[bits[0]+"__Context__"] = cont
        name = cls.clean_symbol_names(name)
        assign_bits = name.split(".")
        if len(assign_bits) == 1:
            env[name] = val
        else:
            assign_obj = eval(".".join(assign_bits[:-2]), env, env)
            setattr(assign_obj, assign_bits[-1], val)

    @classmethod
    def exec_code(cls, args, env):
        # I should probably do something about context handling but I don't
        # really know what...
        if isinstance(args, str):
            args = [ args ]
        for chunk in args:
            chunk = cls.clean_symbol_names(chunk)
            exec(chunk, env, env)



###############################################################################################
#                                                                                             #
#                                           Expr                                              #
#                                                                                             #
###############################################################################################

class Expr:
    """The Expr class is a representation of arbitrary Mathematica expressions in Java.
    Exprs are created by reading an expression from a link (using the getExpr() method),
    they can be decomposed into component Exprs with methods like head() and part(), and
    their structure can be queried with methods like length(), numberQ(), and matrixQ().
    All these methods will be familiar to Mathematica programmers, and their Expr
    counterparts work similarly. Like Mathematica expressions, Exprs are immutable, meaning
    they can never be changed once they are created. Operations that might appear to modify
    an Expr (like delete()) return new modified Exprs without changing the original.
    <p>
    Exprs are stored initially in a very efficient way, and they can be created and written
    to links very quickly. When you call operations that inspect their structure or that
    extract component parts, however, it is likely that they must be unpacked into a more
    Java-native form that requires more memory.
    <p>
    In its present state, Expr has four main uses:
    <p>
    (1) Storing expressions read from a link so that they can be later written to another
    link. This use replaces functionality that C-language programmers would use a loopback
    link for. (J/Link has a LoopbackLink interface as well, but Expr affords an even easier
    method.)
    <pre>
        Expr e = ml.getExpr();
        // ... Later, write it to a different MathLink:
        otherML.put(e);
        e.dispose();</pre>
    Note that if you just want to move an expression immediately from one link to another, you
    can use the MathLink method transferExpression() and avoid creating an Expr to store it.
    <p>
    (2) Many of the KernelLink methods take either a string or an Expr. If it is not convenient
    to build a string of Mathematica input, you can use an Expr. There are two ways to build an
    Expr: you can use a constructor, or you can create a loopback link as a scratchpad,
    build the expression on this link with a series of MathLink put calls, then read
    the expression off the loopback link using getExpr(). Here is an example that creates an Expr
    that represents 2+2 and computes it in Mathematica using these two techniques:
    <pre>
    	// First method: Build it using Expr constructors:
    	Expr e1 = new Expr(new Expr(Expr.SYMBOL, "Plus"), new Expr[]{new Expr(2), new Expr(2)});
     	// ml is a KernelLink
    	String result = ml.evaluateToOutputForm(e1, 72);
    	// Second method: Build it on a LoopbackLink with MathLink calls:
    	LoopbackLink loop = MathLinkFactory.createLoopbackLink();
    	loop.putFunction("Plus", 2);
    	loop.put(2);
    	loop.put(2);
    	Expr e2 = loop.getExpr();
    	loop.close();
    	result = ml.evaluateToOutputForm(e2, 72);
    	e2.dispose();</pre>
    (3) Getting a string representation of an expression. Sometimes you want to be able to
    produce a readable string form of an entire expression, particularly for debugging. The
    toString() method will do this for you:
    <pre>
        // This code will print out the next expression waiting on the link without
        // consuming it, so that the state of the link is unchanged:
        System.out.println("Next expression is: " + ml.peekExpr().toString());</pre>
    (4) Examining the structure or properties of an expression. Although it is possible to
    do this sort of thing with MathLink calls, it is very difficult in general. Expr lets
    you read an entire expression from a link and then examine it using a very high-level
    interface and without having to worry about managing your current position in an
    incoming stream of data.
    <p>
    Expr is a work in progress. It will be expanded in the future.
    """

    __EXPR_TABLE  = {}
    __ALLOW_EMPTY = False

    def __init__(self, *args, loopback = None):

        self.__type   = None
        self.__itype  = None
        self.__dims   = None
        self.__head   = None
        self.__args   = None
        self.__link   = loopback
        self.__hash   = None

        if len(args)>0:
            head = args[0]
            args = args[1:]
            if len(args) == 0:
                self.__init_from_val(head)
            elif isinstance(head, (int, str)) and len(args) == 1:
                self.__init_from_val_and_hint(head, args[0])
            elif isinstance(head, Expr):
                if head.data_type == "Symbol":
                    self.__init_from_head_and_args(head, args)
                else:
                    raise ValueError(
                        "{}: head must be of type 'Symbol' not '{}'".format(type(self).__name__, head.data_type)
                    )
            else:
                raise ValueError(
                    "Unable to construct {} from head {} and args {}".format(type(self).__name__, head, args)
                )
        elif not self.__ALLOW_EMPTY and not loopback:
            raise TypeError("__init__() missing 1 required positional argument: 'val'")
        else:
            self.__type = Env.getExprTypeInt("Unknown")

    @classmethod
    def _get_cached_expr(cls, name, *args):
        try:
            expr = cls.__EXPR_TABLE[name]
        except KeyError:
            expr = cls.__EXPR_TABLE[name] = cls(*args)
        return expr

    @classmethod
    def _get_head(cls, sym):
        return cls._get_cached_expr(sym, "Symbol", sym)

    def __init_from_val(self, val):
        """Create an Expr from the value val

        :param val:
        :return:
        """

        from decimal import Decimal as decimal
        from fractions import Fraction as fraction
        from collections import OrderedDict as Association
        from array import array

        converter_map = {
            int      : { "type" : Env.getExprTypeInt("Integer"), "head" : "Integer" },
            float    : { "type" : Env.getExprTypeInt("Real"), "head" : "Real" },
            str      : { "type" : Env.getExprTypeInt("String"), "head" : "String" },
            decimal  : { "type" : Env.getExprTypeInt("Decimal"), "head" : "Real" },
            fraction : { "type" : Env.getExprTypeInt("Rational"), "head" : "Rational" },
            complex  : { "type" : Env.getExprTypeInt("Complex"), "head" : "Complex" },
        }

        otype  = None
        ohead  = None
        oitype = None
        odims  = None

        for key, item in converter_map.items():
            if isinstance(val, key):
                otype = item["type"]
                ohead = self._get_head(item["head"])
                odims = (0,)
                break

        if otype is None:
            if isinstance(val, BufferedNDArray):
                ohead  = self._get_head("List")
                otype  = Env.getExprTypeInt("BufferedNDArray")
                oitype = val.typecode
                odims  = val.shape
            if isinstance(val, array):
                ohead  = self._get_head("List")
                otype  = Env.getExprTypeInt("Array")
                oitype = val.typecode
                odims  = (len(val), )
            elif isinstance(val, Association):
                ohead = self._get_head("Association")
                otype = Env.getExprTypeInt("Association")
                odims = (len(val), )
            elif isinstance(val, (list, tuple)):
                ohead = self._get_head("List")
                otype = Env.getExprTypeInt("List")
                odims = ArrayUtils.get_array_dims(val, False)
            elif Env.HAS_NUMPY:
                import numpy as np
                if isinstance(val, np.ndarray):
                    ohead  = self._get_head("List")
                    otype  = Env.getExprTypeInt("NumPyArray")
                    oitype = val.dtype.type
                    odims  = val.shape

        if otype is None:
            ohead = self._get_head(type(val).__name__)
            try:
                iter(val) # iterable anything is a list ?
            except:
                otype = self._get_head("Object")
                odims = (0, )
            else:
                otype = Env.getExprTypeInt("Function")
                odims = ArrayUtils.get_array_dims(val, False)

        self.__head  = ohead
        self.__args  = (val, )
        self.__type  = otype
        self.__itype = oitype
        self.__dims  = odims

    def __init_from_val_and_hint(self, typename, val):
        """Creates an Expr representing a Mathematica Integer, Real, String, or Symbol whose value is
given by the supplied string (for example "2", "3.14", or "Plus").

        :param typename: the type of the Expr; must be one of "Integer", "Real", "Decimal", "Fraction", or "Symbol"
        :param val: the value of the Expr, interpreted according to the type argument
        :return:
        """

        if isinstance(typename, int):
            typename = Env.getExprTypeName(typename)

        if typename == "Integer":
            self.__head = self._get_head("Integer")
            self.__args = (int(val), )
            self.__type = Env.getExprTypeInt(typename)
            self.__dims = ()
        elif typename == "Real":
            self.__head = self._get_head("Real")
            self.__args = (float(val), )
            self.__type = Env.getExprTypeInt(typename)
            self.__dims = ()
        elif typename == "String":
            self.__head = self._get_head("String")
            self.__args = (str(val), ),
            self.__type = Env.getExprTypeInt(typename)
            self.__dims = ()
        elif typename == "Symbol":
            import re
            if not isinstance(val, str):
                raise TypeError("{} with head Symbol can't have value of type {}. Only str is allowed".format(type(self).__name__, type(val).__name__))
            val = val.strip()
            sym_re = "($|[^\W\d_])+"
            sym_re = re.compile(sym_re, re.U)
            if not re.match(sym_re, val):
                raise ValueError("Symbol must match regex {}".format(sym_re))

            if val == "Symbol":
                self.__head = self
            else:
                self.__head = self._get_head("Symbol")

            self.__args = (val, )
            self.__type = Env.getExprTypeInt(typename)
            self.__dims = ()
        elif typename == "Rational":
            from fractions import Fraction as fraction
            self.__head = self._get_head("Rational")
            self.__args = (fraction(val), ),
            self.__type = Env.getExprTypeInt(typename)
            self.__dims = ()
        elif typename == "Decimal":
            from decimal import Decimal as decimal
            self.__head = self._get_head("Real")
            self.__args = (decimal(val), ),
            self.__type =  Env.getExprTypeInt(typename)
            self.__dims = ()
        elif typename == "Complex":
            self.__head = self._get_head("Complex")
            self.__args = (complex(val), ),
            self.__type =  Env.getExprTypeInt(typename)
            self.__dims = ()
        elif Env.getExprTypeInt(typename) is not None:
            raise ValueError("{} of type {} cannot be constructed from value".format(type(self).__name__, typename))
        else:
            raise TypeError("Type integer {} unknown for {}".format(typename, type(self).__name__))

    def __init_from_head_and_args(self, head, args):
        if not isinstance(head, Expr):
            raise TypeError("{}: head must be of type Expr not {}".format(type(self).__name__, type(head).__name__))
        self.__head = head
        self.__args = args
        self.__type = Env.getExprTypeInt("Function")

    def _prepareFromLoopback(self):
        if self.__link is not None:
            try:
                self._fillFromLink(self.__link)
            except MathLinkException:
                pass
            finally:
                self.__link.close()
                self.__link = None
        else:
            pass #I guess we don't throw here?

    def _fillFromLink(self, link):
        """Fills out the fields of an existing Expr by reading from a link (typically, but not always, this link is
the Expr's own loopback link that was first used to store its contents).
Up to the caller to ensure that link != null.

       :param link:
       :return:
       """

        typechar = link._getType()
        if isinstance(typechar, int):
            typechar = Env.fromTypeToken(typechar)

        if typechar == "func":
            try:
                argc = link._getArgCount()
                self.__head = head = self.createFromLink(link, False)
                smint = Env.getExprTypeInt("Symbol")
                if head.data_type == smint and head.val == "Rational":
                    self.__init_from_val_and_hint(
                        "Rational",
                        link._getString().strip()+"/"+link._getString().strip()
                    )
                elif head.data_type == smint and head.val == "Complex":
                    self.__init_from_val_and_hint(
                        "Complex",
                        link._getString().strip+"+"+link._getString().strip()+"j"
                    )
                else:
                    self.__type = Env.getExprTypeInt("Function")
                    self.__args = tuple( self.createFromLink(link, False) for i in range(argc) )
            finally:
                link._clearError()


    @classmethod
    def createFromLink(cls, link, allowLoopback = False):
        from .LoopbackLink import LoopbackLink

        typechar = link._getType()
        if isinstance(typechar, int):
            typechar = Env.fromTypeToken(typechar)

        if typechar in ("Integer", "Real", "String", "Symbol"):
            return cls.createAtomicExpr(link, typechar)
        elif allowLoopback and not cls.__ALLOW_EMPTY: # this is intended to prevent infinite recursion
            # This test is "will an attempt to use a loopback link NOT cause the native library to be loaded
            # for the first time?" We want to allow Expr operations to remain "pure Java" as much as possible,
            # so they can be performed on platforms for which no native library is available (e.g., handhelds).
            # We also only use a loopback link if the link we are reading from is a NativeLink. This is because
            # transferExpression() when reading from a non-NativeLink is written in terms of getExpr(), which calls
            # right back here, and we get infinite recursion.
            try:
                with link._wrap(checkError=False, checkLink=False):
                    cls.__ALLOW_EMPTY=True
                    ex = Expr(loopback=LoopbackLink())
                    ex.link.transferExpression(link)
                    return ex
            finally:
                cls.__ALLOW_EMPTY=False
        else:
            res = Expr()
            res._fillFromLink(link)
            return res

    @classmethod
    def createAtomicExpr(cls, link, typechar):

        og = typechar
        if isinstance(typechar, int):
            typechar = Env.fromTypeToken(typechar)

        if typechar == "Integer":
            return cls("Integer", link._getString())
        elif typechar == "Real":
            dub = link._getString()
            dub = dub.replace(",", ".")
            try:
                dub = float(dub)
            except:
                from decimal import Decimal
                dub = Decimal(dub)
            return cls("Real", dub)
        elif typechar == "String":
            return cls("String", link._getString())
        elif typechar == "Symbol":
            return cls("Symbol", link._getString())
        elif typechar == "Decimal":
            return cls("Decimal", link._getString())
        elif typechar == "Rational":
            return cls("Rational", link._getString())
        else:
            raise ValueError("{}: no atomic type {} to work with".format(cls.__name__, og))

    def put(self, link):
        if self.__link is not None:
            mark = self.__link._createMark()
            try:
                link._transferExpression(self.__link)
            finally:
                link._clearError()
                self.__link._seekMark(mark)
                self.__link._destroyMark(mark)
        else:
            tname = Env.getExprTypeName(self.__type)
            if tname == "Symbol":
                link.putSymbol(self.val)
            elif tname == "Function":
                link._putNext(Env.toTypeToken("Function"))
                link._putArgCount(len(self))
                link.put(self.head)
                for a in self.__args:
                    link.put(a)

    @property
    def head(self):
        self._prepareFromLoopback()
        return self.__head
    @property
    def data_type(self):
        self._prepareFromLoopback()
        return self.__type
    @property
    def item_type(self):
        self._prepareFromLoopback()
        return self.__itype
    @property
    def val(self):
        self._prepareFromLoopback()
        return self.__args[0] if len(self.__args) > 0 else None
    @property
    def args(self):
        self._prepareFromLoopback()
        return self.__args
    @property
    def link(self):
        return self.__link

    def __calc_dims(self):
        if self.__type == Env.getExprTypeInt("Function"):
            self.__dims = ArrayUtils.get_array_dims(self.__args, Env.HAS_NUMPY)
        elif self.__type in map(Env.getExprTypeInt, ("Integer", "Real", "Decimal", "Complex", "String", "Symbol")):
            self.__dims = ()
        elif self.__type in map(Env.getExprTypeInt, ("BufferedNDArray", "NumPyArray")):
            self.__dims = self.__args[0].shape
        elif self.__type == Env.getExprTypeInt("List"):
            self.__dims = ArrayUtils.get_array_dims(self.__args, Env.HAS_NUMPY)
        else:
            raise ValueError("{}: unable to determine dimension for type {}".format(type(self).__name__, Env.getExprTypeName(self.__type) ) )
        return self.__dims

    def dimensions(self):
        if self.__dims is None:
            self.__calc_dims()
        return tuple(self.__dims)

    def toJSON(self):
        raise NotImplemented

    def writeObject(self, output_stream):
        self._prepareFromLoopback()
        return output_stream.defaultWriteObject()

    def readObject(self, input_stream):
        return input_stream.defaultReadObject()

    @property
    def cached_hash(self):
        return self.__hash

    def __hash__(self):
        if self.__hash is None:
            self.__hash = hash((self.__head.val, self.args))
        return self.__hash

    def __eq__(self, other):

        if self is other:
            return True
        if not isinstance(other, type(self)):
            return False

        # I'm dropping the prepareFromLoopback calls made in the JLink source because I force
        # a prepareFromLoopback in construction generally

        if self.cached_hash == other.cached_hash:
            return True

        if self.data_type != other.data_type or \
                self.head is not other.head or \
                self.dimensions() != other.dimensions():
            return False

        return self.args == other.args

    def part(self, key):
        raise NotImplemented

    def __getitem__(self, key):
        self.part(key)

    def __setitem__(self, key, value):
        pass

    def length(self):
        if self.__type == Env.getExprTypeInt("Function"):
            return len(self.__args)
        else:
            return len(self.__args[0])
    def __len__(self):
        return self.length()

    def __str__(self):
        if self.__head in map(self._get_head, ["Symbol", "Integer", "Real", "Rational", "Decimal"]):
            return self.val
        elif self.__head == self._get_head("String"):
            return '"{!r}"'.format(self.val)
        elif self.__head == self._get_head("List"):
            def rec_stringify(o):
                if isinstance(o, (list, tuple)): # intentionally only doing these two iterables
                    return "{" + ", ".join(rec_stringify(x) for x in o) + "}"
                else:
                    return str(o)
            return rec_stringify(list(self.val))
        elif self.__head == self._get_head("Association"):
            return "<|" + ", ".join("{}->{}".format(*pair) for pair in self.val.items()) + "|>"
        else:
            return "{}[{}]".format(self.__head, ", ".join(map(str, self.__args)))