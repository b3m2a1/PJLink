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
# def expr_repr(expr):
#     return "{}[{}]".format(expr.head, ", ".join(repr(x) for x in expr.args))
# expr_repr.name = "__repr__"
# MLExpr.__repr__ = expr_repr
# del expr_repr
###############################################################################################
#                                            MLExpr                                           #
MLExpr             = namedtuple("MLExpr",             ["head", "args", "end"])
MLExpr.__new__.__defaults__ = (False,)
def expr_repr(expr):
    return "{}[{}]".format(expr.head, ", ".join(repr(x) for x in expr.args))
expr_repr.name = "__repr__"
MLExpr.__repr__ = expr_repr
del expr_repr
###############################################################################################
#                                            MLSym                                            #
MLSym              = namedtuple("MLSym",              ["name"]            )
def sym_repr(sym):
    return "{}".format(sym.name)
sym_repr.name = "__repr__"
MLSym.__repr__ =sym_repr
del sym_repr
def call_sym(sym, *args, **kwargs):
    return MExprUtils.F(sym.name, *args, **kwargs)
MLSym.__call__=call_sym
del call_sym
###############################################################################################
#                                            MLUnevaluated                                    #
MLUnevaluated      = namedtuple("MLUnevaluated",      ["arg"]             )
def uneval_repr(uneval):
    return "{}".format(uneval.arg)
uneval_repr.name = "__repr__"
MLUnevaluated.__repr__ = uneval_repr
del uneval_repr
###############################################################################################
#                                            PacketArrivedEvent                               #
PacketArrivedEvent = namedtuple("PacketArrivedEvent", ["packet", "link"]  )
###############################################################################################
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

    @property
    def data(self):
        mm = memoryview(self._buffer)
        mm = mm.cast("B")
        return mm.cast(self.typecode, self.shape)

    @property
    def itemsize(self):
        return self._buffer.itemsize
    def byteswap(self):
        return self._buffer.byteswap()
    def buffer_info(self):
        return self._buffer.buffer_info()

    def copy(self):
        return type(self)(self._buffer.copy(), self.__shape, self.__offsets)

    def astype(self, typestr):
        import array

        tnames = {
            "int8" : "b", "uint8" : "B",
            "int16" : "h", "uint16" : "H",
            "int32" : "i", "uint32" : "I",
            "int64" : "l", "uint64" : "L",
            "float32" : "f", "float64" : "d"
        }
        if typestr in tnames:
            typestr = tnames[typestr]

        cast = array.array(typestr, self._buffer)

        return type(self)(cast, self.__shape, self.__offsets)

    @classmethod
    def from_buffers(cls, buffs, dims = None):
        if dims is None:
            dims = [ len(b) for b in buffs ]
        bob = None
        for b in buffs:
            if bob is None:
                bob = cls(b, dims)
            else:
                bob.extend(b)
        bob.adjust()
        return bob

    @classmethod
    def from_iterable(cls, itable, dims = None):
        import array

        if dims is None:
            dims = [ len(itable) ]

        if isinstance(itable, str):
            tchar = 'B'
            itt = itable
        else:
            itt = list(itable)
            tchar = None
            if isinstance(itt[0], int):
                tchar = 'l'
            elif isinstance(itt[0], float):
                tchar = 'd'
            elif isinstance(itt[0], (bytes, bytearray)):
                tchar = 'B'
            else:
                raise TypeError("{}: couldn't determine typecode for object '{}'".format(cls.__name__, itt[0]))

        return cls(array.array(tchar, itt), dims)

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
        blen = len(self._buffer)
        end = len(self._buffer) - elems
        if 0 > end:
            raise ValueError("Buffer dimension exceeds buffer size")
        elif start >= blen or end >= blen:
            raise ValueError("Buffer offset exceeds buffer size")
        elif end < 0 or start < 0:
            raise ValueError("Buffer offset cannot be negative")
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
    def ndim(self):
        return len(self.__shape)

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

    @property
    def depth(self):
        return len(self.__shape)

    def __len__(self):
        return self.__shape[0]

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

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
            bob.adjust()
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
            bob.adjust()
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
        shape = self.shape
        if len(shape) == 1 and isinstance(ind, (int, slice)):
            return self._buffer[self.__offsets[0]:len(self._buffer)-self.__offsets[1]][ind]
        else:
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
        shape = self.shape
        if len(shape) == 1 and isinstance(ind, (int, slice)):
            if isinstance(ind, slice):
                sta = self.__offsets[0] + 0 if ind.start is None else ind.start
                sto = (len(self._buffer)-self.__offsets[0]) + 0 if ind.stop is None else ind.stop
                ste = ind.step
                ind = slice(sta, sto, ste)
            else:
                ind = self.__offsets[0] + ind

            self._buffer[ind] = value
        else:
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
    def __init__(self, parent, checkLink = True, checkError = True, check = None, lock = True, timeout = None, poll = 20):
        self.parent     = parent
        self.check      = check
        self.checkLink  = checkLink
        self.checkError = checkError
        self.lock       = lock
        self.timeout    = timeout
        self.poll_rate  = poll
        self.__started  = None
        self.__locked   = False
        self.__thread   = None

    def poll(self):
        import time, threading

        if self.__started is None:
            self.__started = time.time()

        if self.timeout:
            if time.time() - self.__started > 1000*self.timeout:
                # Env.logf("Aborting wrap call")
                self.__exit__(None, None, None)
            else:
                if self.__thread is None:
                    self.__thread = threading.Thread(target=self.poll)
                    self.__thread.start()

                time.sleep(self.poll_rate/1000)

        elif self.__started:
            self.__exit__(None, None, None)

    def __enter__(self):

        if self.checkLink:
            self.parent._check_link()
        if self.lock:
            self.__locked = True
            import threading
            # Env.logf("Locking thread {}", threading.current_thread())
            self.parent.thread_lock.acquire()

        if self.timeout:
            self.poll()

        return self

    def __exit__(self, type, value, traceback):
        if self.__thread is not None:
            self.timeout = None
        if self.__locked:
            import threading
            # Env.logf("Unlocking thread {}", threading.current_thread())
            self.parent.thread_lock.release()
        if self.checkError:
            self.parent._check_error(self.check)

###############################################################################################
#                                                                                             #
#                                          LinkMark                                           #
#                                                                                             #
###############################################################################################

class LinkMark:
    """A wrapper to allow with ...: syntax to set a mark on a link

    """
    def __init__(self, parent, seek = False):
        self._parent = parent
        self._mark = None
        self._seek = seek
        self._destroyed = False

    def init(self):
        self._mark = self._parent._createMark()
        return self

    def seek(self):
        self._parent._seekMark(self._mark)

    def destroy(self):
        if not self._destroyed:
            self._parent._destroyMark(self._mark)
            self._destroyed = True

    def revert(self):
        if not self._destroyed and self._mark is not None:
            if self._seek:
                self.seek()
            self.destroy()

    def __enter__(self):
        return self.init()
    def __exit__(self, type, value, traceback):
        self.revert()

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
    def nones(dims):
        # this is an ugly, gross, dangerous hack but also only like two lines of code...
        # could also do via http://code.activestate.com/recipes/577061-nest-a-flat-list/
        # all methods will be slow, unfortunately... (hence BufferedNDArray)

        meta = 'None'
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
            raise TypeError("MathLink can only handle homogenous type data but got data of type {} and of type {}".format(array_type, test_array_type_int))

        if isinstance(test_array_type, int):
            res = item
        elif isinstance(test_array_type, str):
            try:
                res = array.array(test_array_type, item)
            except ValueError:
                raise TypeError("MathLink can only handle homogenous type data but got data of type {} and array {}".format(test_array_type, item))
        else:
            raise TypeError("MathLink can't handle data of type {}".format(type(item[0]).__name__))

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

            if not res.data.c_contiguous:
                res = np.ascontiguousarray(np)
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

            array_type, item_arr = cls.get_array_object(array_type, item)

            if isinstance(item_arr, array.array):
                res = BufferedNDArray(item_arr, dims)
            elif len(dims) == 1:
                res = item_arr
            else:
                res = cls.nones(dims)
                rl = res
                for i in index:
                    if rl[i] is not None:
                        rl = rl[i]
                rl[i]=item_arr

            for index in index_iter:
                # maybe I could do this more efficiently by not reindexing, but I don't
                # know how to get this kind of thing working well here

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

                array_type, item_arr = cls.get_array_object(array_type, item)

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
            depth = 0
            do = ob
            try:
                while hasattr(do, "__getitem__"):
                    if isinstance(do, str):
                        break
                    do2 = do[0] # a good further test that it's indexable
                    if do2 == do:
                        break
                    do = do2
                    depth += 1
            except Exception as e:
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
    PackagePrivate = PackageContext+"Private`"
    PackagePackage = PackageContext+"Package`"

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
        return cls.List(*opts)

    @classmethod
    def _symbol(cls, name):
        return MLSym(name)
    S =  _symbol

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
        return MLExpr("Set", ( MLSym(lhs) if isinstance(lhs, str) else lhs, rhs) )
    @classmethod
    def SetDelayed(cls, lhs, rhs):
        return MLExpr("SetDelayed", ( MLSym(lhs) if isinstance(lhs, str) else lhs, rhs))
    s  = Set
    sd = SetDelayed
    @classmethod
    def Unset(cls, lhs, rhs):
        return MLExpr("Unset", (lhs, rhs))
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
            cls.List(*cpath)
            )
    @classmethod
    def restore_context_path(cls):
        return cls.F("System`Private`RestoreContextPath")
    @classmethod
    def with_context(cls, context, cpath, expr):
        setup = [
            cls.Set(cls._prsym("cachedContext"), MLSym("$Context"))
        ]
        teardown = [
            cls.Set(MLSym("$Context"), cls._prsym("cachedContext"))
        ]
        if context is not None:
            setup.append(cls.Set(MLSym("$Context"), context))
            # teardown.append(cls.s(MLSym("$Context"), context))
        if cpath is not None:
            setup.append(cls.new_context_path(cpath))
            teardown.append(cls.restore_context_path())

        return cls.setup_teardown(
            cls.do(*setup),
            expr,
            cls.do(*teardown)
        )

    None_ = MLSym("None")
    Failed_ = MLSym("$Failed")
    Aborted_ = MLSym("$Aborted")
    Canceled_ = MLSym("$Canceled")


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

        if hasattr(cls, fname):
            return None

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

    def from_dict(self, expr):
        head = expr["_head"]
        args = expr["_args"]
        try:
            kwargs = expr["_opts"]
        except KeyError:
            kwargs = {}

        argnew = [ None ] * len(args)
        for i, a in enumerate(args):
            if isinstance(a, dict):
                if "_head" in dict and "_args" in dict:
                    argnew[i] = self.from_dict(a)
                elif "_symbol" in dict:
                    argnew[i] = self.S(a["_symbol"])
                else:
                    argnew[i] = a

        return self.F(head, *args, **kwargs)


###############################################################################################
#                                                                                             #
#                                     MExprUtilsConfig                                        #
#                                                                                             #
###############################################################################################

# MExprUtils.register_function("Needs", "pkg", "file___")
# MExprUtils.register_function("Get", "pkg")
# MExprUtils.register_function("Import", "file", "fmt___", OptionsPattern=True)
# MExprUtils.register_function("Export", "file", "expr", "fmt___", OptionsPattern=True)
# MExprUtils.register_function("ExportString", "expr", "fmt___", OptionsPattern=True)

MExprUtils.register_function("Which", "test1", "body1", "testBodies___")
MExprUtils.register_function("Switch", "type", "pat1", "body1", "patBodies___")
MExprUtils.register_function("If", "test", "true", "false", "indet___")

MExprUtils.register_function("ToString", 'expr', FormatType_=None, PageWidth_=None, OptionsPattern=True)
MExprUtils.register_function("ToBoxes", 'expr', "fmt___")
MExprUtils.register_function("ToExpression", 'str', "fmtHead___")

# for pkt in (
#     "Illegal", "Call", "Evaluate",
#     "Return", "InputName", "EnterText",
#     "EnterExpression", "OutputName", "ReturnText",
#     "ReturnExpression", "Display", "DisplayEnd",
#     "Message", "Text", "Input", "InputString", "Menu",
#     "Syntax", "Suspend", "Resume", "BeginDialog", "EndDialog",
#     "Expression"
#     ):
#     MExprUtils.register_function(pkt+"Packet", "expr___")

###############################################################################################
#                                                                                             #
#                                        MPackage                                             #
#                                                                                             #
###############################################################################################

class MPackageClass(MExprUtils):
    """MPackage is a class that holds high-level package functions lifted from JLink for use in PJLink

    """

    JLinkContext           = "JLink`"
    JLinkEvaluateToContext = JLinkContext + "EvaluateTo`"
    PackageTypeHints = MExprUtils.PackageContext + "TypeHints`"
    __The_One_True_Package = None

    import os
    _package_WL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Mathematica", "PJLink.wl")
    __sym_list = os.path.join(os.path.dirname(__file__), "Resources", "sym_list.json")
    del os

    def __init__(self):
        if self.__The_One_True_Package is not None:
            raise TypeError("MPackageClass is not intended to be a single instance class")
        self.__The_One_True_Package = self
        self.__initialized = False
        self.__symbols = None

    @property
    def symbol_list(self):
        return self.__symbols

    @classmethod
    def in_package(cls, expr):
        return cls.with_context(
            cls.PackagePackage,
            ["System`", cls.PackageContext, cls.PackagePackage, cls.PackagePrivate],
            expr
        )

    def initialize_from_list(self, names):
        if not self.__initialized:
            self.__initialized = True
            kd = self.__dict__
            pd = MExprUtils.__dict__
            self.__symbols = [ None ]*len(names)
            for i, namePair in enumerate(names):
                name, sym = namePair
                self.__symbols[i] = (name, MLSym(sym))
                if name not in kd and name not in pd: #constant time lookup hopefully
                    setattr(self, name, MLSym(sym))
            self.__symbols = tuple( s for s in self.__symbols if s is not None )
            return True
        else:
            return False

    def initialize_from_file(self, file):
        if not self.__initialized:
            with open(file) as f:
                import json
                names = json.load(f)
                return self.initialize_from_list(names)
        else:
            return False
    def initialize_from_link(self, link):
        if not self.__initialized:
            names = link.evaluate(self.Select(self.Names["System`*"], self.PrintableASCIIQ))
            return self.initialize_from_file(names)
        else:
            return False
    def initialize_default(self):
        return self.initialize_from_file(self.__sym_list)

    def to_Association(self, expr):
        return self.Association(*(self.Rule(*rule) for rule in expr.items()))
    def to_HashTable(self, expr):
        try:
            _version = expr[ "_HashTable_version_" ]
        except KeyError:
            _version = 1
        return self.System_Utilities_HashTable(_version, *(list(rule) for rule in expr.items()))
    def to_Rules(self, expr):
        return self.List(*(self.Rule(*rule) for rule in expr.items()))

    def _get_obj_name_sym(self, obj):
        return obj.__qualname__.replace(".", "`")

    def prep_object(self, o, link, coerce = False):
        enc = link.Converter.encode(o, link)
        link.Env.logf("Encoded object {}. Coersion? {}", enc, coerce)
        return self.get_puttable(enc, link, coerce=coerce)

    def get_puttable(self, o, link, coerce = False):

        from collections import OrderedDict
        from types import ModuleType, CodeType, FunctionType

        if not isinstance(o, MPackageClass) and hasattr(o, "expr"):
            expr = o.expr
            if callable(expr):
                expr = expr(link)
            o = expr

        if isinstance(o, dict):
            try:
                expr = self.from_dict(o)
            except KeyError:
                expr = None
            if isinstance(expr, MLExpr):
                o = expr

        # TODO: write an actual framework for encoding these generally
        if isinstance(o, OrderedDict):
            o = self.to_Association(o)
        elif isinstance(o, dict):
            o = self.to_HashTable(o)
        elif isinstance(o, FunctionType):
            o = self.to_FunctionObject(o)
        elif isinstance(o, CodeType):
            o = self.to_CodeObject(o)
        elif isinstance(o, type):
            o = self.to_ClassObject(o)
        elif isinstance(o, ModuleType):
            o = self.to_ModuleObject(o)
        elif coerce:
            o = self.to_ObjectInstance(o)

        return o

    def to_ModuleObject(self, mdl):
        head = self.PJLink_ModuleObject
        body = OrderedDict([
            ("name", mdl.__name__),
            ("attributes", list(vars(mdl)))
        ])
        return head(self.to_Association(body))

    def to_ClassObject(self, cls):
        head = self.PJLink_TypeObject
        body = OrderedDict([
            ("type", self._get_obj_name_sym(cls)),
            ("attributes", list(vars(cls)))
        ])
        return head(self.to_Association(body))

    def to_CodeObject(self, expr):
        import inspect
        head = self.PJLink_CodeObject

        name = expr.co_name
        file = expr.co_filename
        lineno = expr.co_firstlineno

        try:
            body = inspect.getsource(expr)
        except:
            body = self.Missing("BodyUnavailable")

        return head(
            self.to_Association(
                OrderedDict([
                    ("name", name),
                    ("file", file),
                    ("line", lineno),
                    ("body", body)
                ])
            )
        )

    def to_FunctionObject(self, expr):
        head = self.PJLink_FunctionObject
        name = expr.__code__.co_name
        var_names = expr.__code__.co_varnames
        try:
            argc = expr.__code__.co_argcount
        except AttributeError:
            argc = 0
        try:
            kwc = expr.__code__.co_kwonlycount
        except AttributeError:
            kwc = 0
        return head(
            self.to_Association(
                OrderedDict([
                    ("name", name),
                    ("arguments", var_names),
                    ("args", argc),
                    ("kwargs", kwc)
                ])
            )
        )

    def to_ObjectInstance(self, expr):
        t = type(expr)
        head = self.PJLink_ObjectInstance
        cls = self._get_obj_name_sym(t)
        args = OrderedDict([("type", cls)])
        try:
            body = vars(expr)
            args["attributes"] = list(body.keys())
        except TypeError:
            try:
                body = list(expr)
                try:
                    body.remove(expr) # recursion sucks
                except:
                    pass
                args["body"] = body
            except:
                body = repr(expr)
                args["repr"] = body

        return head(self.to_Association(args))

    def to_ElidedForm(self, expr, maxlen):
        els = list(expr)
        total_len = len(els)
        taken_els = els[:maxlen]
        taken_els.append(self.Skeleton(total_len - maxlen))
        return taken_els

    def _add_type_hints(self, to_eval):
        return self.CompoundExpression(
            self._load_PJLink(),
            self.F(self.PackageTypeHints+"AddTypeHints", to_eval)
        )

    def _eval(self, expr, add_type_hints = True):
        return self.EvaluatePacket(expr, _EndPacket=True)

    def __get_evaluate_to_parameters(self, obj, page_width, format):
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

        return self.ToExpression(obj) if isinstance(obj, str) else obj, page_width, MLSym(format)

    def _load_JLink(self):
        return self.Needs(self.JLinkContext)

    def _load_JLink_packet(self):
        return self._eval(self._load_JLink())

    def _load_PJLink(self):
        return self.Needs(self.PackageContext, self._package_WL)

    def _to_cell_expr(self, obj, page_width = None, format = None, **kw):
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
        obj, page_width, format = self.__get_evaluate_to_parameters(obj, page_width, format)
        expr = MLSym("expr")
        kw.update(ShowCellBracket_=False, CellMargins_=[[0, 0], [0, 0]], PageWidth_=page_width)
        return self.Block(
            {
                "$DisplayFunction_" : MLSym("Identity"),
                "expr"   : None
            },
            self.Set(expr, obj),
            self.Switch(expr,
                self.Blank("Cell"),    expr,
                self.Blank("BoxData"), self.F("Cell", expr, "Output", *kw),
                self.Blank(),          self.F("Cell", self.ToBoxes(expr, format), "Output", *kw)
             )
        )

    def _front_end_shared_q(self):
        return self.F("SameQ", self.F("Head", MLSym("MathLink`ServiceLink")), MLSym("LinkObject"))

    def _eval_to_string(self, obj, page_width=None, format=None, **ops):
        obj, page_width, format = self.__get_evaluate_to_parameters(obj, page_width, format)
        return self.ToString(obj, FormatType = format, PageWidth = page_width, **ops)

    def _eval_to_typset_string(self, obj, page_width = None, format = None, export_format = None, **kw):
        """Python rep of:
             Block[
                {cellExpr, result},
                cellExpr = JLink`ConvertToCellExpression[e, frm, pageWidth, opts];
                ExportString[cellExpr, format]
              ];
        """

        expr_packet = self._to_cell_expr(obj, page_width, format, **kw)
        expr = MLSym("cellExpr")
        if export_format is None:
            export_format = "GIF"
        return self.with_context(
            self.PackagePrivate,
            [ self.PackagePrivate, "System`" ],
            self.Block(
                [ "cellExpr", "res" ],
                self.Set(expr, expr_packet),
                self.Set(MLSym("res"), self.F("ExportString", expr, export_format, **kw))
                )
            )

    def _eval_to_image_string(self, obj, export_format = None, **kw):
        """Python rep of:
             ExportString[cellExpr, format, ops]
        """

        if export_format is None:
            export_format = "GIF"
        return self.F("ExportString", obj, export_format, **kw)
    def _eval_to_image_data(self, obj, **kw):
        return self.F("ImageData", self.F("Rasterize", obj, **kw))

    def _eval_to_string_packet(self, obj, page_width=None, format=None, **ops):
        return self._eval(self._eval_to_string(obj, page_width=page_width, format=format, **ops))

    def _eval_to_typeset_packet(self, obj, page_width=None, format=None, export_format=None, **ops):
        return self._eval(self._eval_to_typset_string(obj, page_width=page_width, format=format, export_format = None, **ops))

    def _eval_to_image_string_packet(self, obj, export_format=None, **ops):
        return self._eval(self._eval_to_image_string(obj, export_format = None, **ops))

    def _eval_to_image_packet(self, obj, **ops):
        return self._eval(self.Rasterize(obj, **ops))

    def __getattr__(self, sym):
        if sym.endswith("_"):
            sym = sym.split("_")[:-1]
            sym[-1] = "$" + sym[-1]
            sym = "`".join(sym)
        else:
            sym = sym.strip("_")
        sym = sym.replace("_", "`")
        return MLSym(sym)

MPackage = MPackageClass()

###############################################################################################
#                                                                                             #
#                                       LinkEnvironment                                       #
#                                                                                             #
###############################################################################################
class LinkEnvironment:


    def __init__(self, link, update_globals = True, update_locals = False):
        self.__env = link._EXEC_ENV
        self.__ug = update_globals
        self.__ul = update_locals

    def get_frame(self, frames_back = 0):
        import inspect

        frame = inspect.currentframe()
        for i in range(frames_back+1):
            frame = frame.f_back

        return frame

    def attach_global(self, frames_back = 0, frame = None):

        if frame is None:
            frame = self.get_frame(frames_back+1)
        glob = frame.f_back.f_globals
        # print(glob.keys())
        glob.update(self.__env)
        self.__cached_keys = set(glob.keys())

    def detach_global(self, frames_back = 0, frame = None):

        if frame is None:
            frame = self.get_frame(frames_back+1)

        glob = frame.f_globals # this is pretty disgusting...

        now_keys = set(glob.keys())
        env_keys = set(self.__env)
        new_keys = now_keys - self.__cached_keys

        for k in new_keys:
            self.__env[k] = glob[k]
            del glob[k]
        for k in env_keys: # slow but without a batch key-remove function not much to be done
            del glob[k]

    def attach_local(self, frames_back = 0, frame = None):

        if frame is None:
            frame = self.get_frame(frames_back+1)

        loc = frame.f_locals # this is pretty disgusting...
        loc.update(self.__env)
        self.__cached_keys = set(loc.keys())

    def detach_local(self, frames_back = 0, frame = None):

        if frame is None:
            frame = self.get_frame(frames_back+1)

        loc = frame.f_locals # this is pretty disgusting...

        now_keys = set(loc.keys())
        env_keys = set(self.__env)
        new_keys = now_keys - self.__cached_keys

        for k in new_keys: # slow but without a batch key-remove function not much to be done
            self.__env[k] = loc[k]
            del loc[k]
        for k in env_keys:
            del loc[k]

    def __enter__(self):
        if self.__ul:
            self.attach_local(frames_back=0)
        elif self.__ug:
            self.attach_global(frames_back=0)

        return self.__env

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__ul:
            self.detach_local(frames_back=1)
        elif self.__ug:
            self.detach_global(frames_back=1)

###############################################################################################
#                                                                                             #
#                                      MathematicaBlock                                       #
#                                                                                             #
###############################################################################################
class MathematicaBlock:

    __sym_dict = {}

    def __init__(self, update_globals = True, update_locals = False):
        self.__ug = update_globals
        self.__ul = update_locals

    def ensure_init(self):
        if MPackage.initialize_default():
            self.__sym_dict.update(dict(MPackage.symbol_list))
            self.__sym_dict.update((("M", MPackage), ("Sym", MPackage)))

    def get_frame(self, frames_back = 0):
        import inspect

        frame = inspect.currentframe()
        for i in range(frames_back+1):
            frame = frame.f_back

        return frame

    def attach_global(self, frames_back = 0, frame = None):

        if frame is None:
            frame = self.get_frame(frames_back+1)

        self.ensure_init()

        glob = frame.f_globals # this is pretty disgusting...
        glob.update(self.__sym_dict)

    def detach_global(self, frames_back = 0, frame = None):

        if frame is None:
            frame = self.get_frame(frames_back+1)

        glob = frame.f_globals # this is pretty disgusting...
        for k in self.__sym_dict: # slow but we should try to keep __sym_dict small anyway
            del glob[k]

    def attach_local(self, frames_back = 0, frame = None):

        if frame is None:
            frame = self.get_frame(frames_back+1)

        self.ensure_init()
        loc = frame.f_locals # this is pretty disgusting...
        loc.update(self.__sym_dict)

    def detach_local(self, frames_back = 0, frame = None):

        if frame is None:
            frame = self.get_frame(frames_back+1)

        loc = frame.f_locals # this is pretty disgusting...
        for k in self.__sym_dict: # slow but we should try to keep __sym_dict small anyway
            del loc[k]

    def __enter__(self):
        if self.__ul:
            self.attach_local(frames_back=1)
        elif self.__ug:
            self.attach_global(frames_back=1)
        else:
            self.ensure_init()

        return self.__sym_dict

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__ul:
            self.detach_local(frames_back=1)
        elif self.__ug:
            self.detach_global(frames_back=1)

###############################################################################################
#                                                                                             #
#                                       TypeConverter                                         #
#                                                                                             #
###############################################################################################

# MStruct = namedtuple("MStruct", ["head", "type", "dimensions", "data"])
class MDecoder(namedtuple("MDecoder", ["head", "type", "dimensions"])):
    """This is an experimental system to make it easy to decode Mathematica structures as
    python types by leveraging the power of namedtuple to get easy representations of this data

    """
    __slots__ = ()
    def get_data(self, link, head, stack):

        otype = self.type
        if callable(otype):
            otype = otype(head, link, stack)

        dims = self.dimensions
        if callable(dims):
            dims = dims(head, link, stack)

        if dims is not None:
            dims = tuple(dims)

        if otype is None or otype=="Function":
            dats = link.get()
        elif dims == () or dims is None:
            dats = link._getSingleObject(otype)
        elif dims == (0,):
            dats = []
        else:
            link.Env.log(otype, dims)
            dats = link._getArray(otype, len(dims))

        return dats #MStruct(dims, otype, head, dats) #I'd return this but I can't foresee it being useful...

    def decode(self, link, stack):

        head = self.head
        if callable(head):
            head = head(link, stack)
        data = None
        try:
            if head is not None:
                sym = link._getSymbol()
                symname = sym.name
                if (isinstance(head, str) and symname.split("`")[-1] == head) or symname in head:
                    data = self.get_data(link, sym, stack)
            else:
                data = self.get_data(link, None, stack)

        except MathLinkException as e:
            data = None

        return data

class StructBase: #This is separate from ObjectDecoder because I might want a DecodedObject type
    __slots__ = ("_name", "_fields", "_vals", "__odict")
    def __init__(self, name, *fields):
        from collections import OrderedDict
        self.__odict = OrderedDict(fields)
        self._fields = tuple( x[0] for x in fields )
        self._vals   = tuple( x[1] for x in fields )
        self._name = name
    def asodict(self):
        return self.__odict.copy()
    def __iter__(self):
        return zip(self._fields, self._vals)
    def __len__(self):
        return len(self._fields)
    def __getattr__(self, attr):
        try:
            return self.__odict[attr]
        except KeyError:
            pass
    def __repr__(self):
        return "{}({})".format(self._name,
                    ", ".join([ "{}= {}".format(name, val) for name, val in self])
                    )

def namedstruct(name, *items):
    items = list(items)
    return namedtuple(name, [ x[0] for x in items] )(*(x[1] for x in items))

class ObjectDecoder(StructBase):
    __slots__ = StructBase.__slots__ + ("_head", "_target")
    def __init__(self, name, head, *fields, target = namedstruct):

        self._head = head
        pars = [ None ] * len(fields)
        for i, dec in enumerate(fields):
            name, dec = dec
            if hasattr(dec, "decode"):
                pars[i] = (name, dec)
            else:
                head, type, dims = dec
                pars[i] = (name, MDecoder(head, type, dims))
        super().__init__(name, *pars)
        self._target = target

    def serialize(self):
        imports = {
            "from {} import {}".format(".".join( [ type(x).__module__ ] + type(x).__qualname__.split(".")[:-1] ), type(x).__name__) for x in self._vals
        }
        dec_str = "_decoder = {}('{}', {}, target = {})".format(type(self).__name__, self._name, ", ".join([ "{}= {}".format(name, val) for name, val in self]), self._target)
        return "\n".join(imports) + "\n\n" + dec_str

    def check_function(self, link):
        head = self._head
        try:
            if head is not None:
                fn = link._getFunction()
                # link.Env.logf("Decoding function {}", fn)
                sym = fn.head
                argc = fn.argCount
                # link.Env.log(sym.split("`")[-1], head, argc, len(self))
                head_right = (isinstance(head, str) and sym.split("`")[-1] == head) or sym in head
                field_count = argc >= len(self)
                valid = head_right and field_count
                # link.Env.log(valid)
            else:
                valid = False

        except MathLinkException as e:
            valid = False

        return valid

    def decode(self, link):
        """This is still somewhat up in the air... the long-term goal is that a decoder will be a set
       of MDecoder or ObjectDecoder objects which unwraps intelligently. Note that all an object
       needs to be a decoder is a 'decode' method so we can subclass the ObjectDecoder for special
       types easily.

       :param link:
       :param decoder:
       :return:
       """
        from collections import OrderedDict

        if self.check_function(link):
            stack = OrderedDict()
            for name, decoder in self:
                # link.Env.log(decoder)
                tres = decoder.decode(link, stack)
                link.Env.log(tres)
                stack[name] = tres
            res = self._target(self._name, *stack.items())
        else:
            res = None
        return res

class ObjectEncoder(StructBase):
    Failed = namedtuple("Failed", [])
    __slots__ = StructBase.__slots__ + ("_type", "_encode")
    def __init__(self, name, type, encode):
        self._type = type
        self._encode = encode
        super().__init__(name)

    def encode(self, o, link):
        if not isinstance(self._type, type):
            raise TypeError("{} is not a type".format(self._type))
        if isinstance(o, self._type):
            return self._encode(o, link)
        return self.Failed

from collections import OrderedDict
class TypeConverter:
    import os
    _base_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "Resources"
    )
    del os

    def __init__(self, *decoders):

        self.decoders = OrderedDict()
        self.encoders = OrderedDict()

        self.load_decoders()
        for name, decoder in decoders:
            if not isinstance(decoder, ObjectDecoder):
                decoder = ObjectDecoder(decoder)
            self.decoders[name] = decoder
        self.load_encoders()
        # Env.logf("Loaded decoders {} and encoders {}", self.decoders, self.encoders)

    def decode(self, link):
        """Attempts to decode the objects on link with all the decoders built in

        """
        with LinkMark(link) as mark:
            for decoder in self.decoders.values():
                try:
                    res = decoder.decode(link)
                except Exception as e:
                    mark.seek()
                    raise

                if res is None:
                    mark.seek()
                else:
                    break
            else:
                res = None
        return res

    def load_decoders(self, path = None):
        import os

        if path is None:
            path = os.path.join(self._base_path, "Decoders")

        for f in os.listdir(path):
            if f.endswith(".py"):
                f, ext = os.path.splitext(os.path.basename(f))
                decoder = self.load_decoder(f, path = path)
                if decoder is not None:
                    self.decoders[f] = decoder

    def load_decoder(self, name, path = None):
        import os

        if os.path.isfile(name):
            decoder_file = name
        elif path is None:
            path = self._base_path
            decoder_file = os.path.join(path, "Decoders", name+".py")
        else:
            decoder_file = os.path.join(path, name+".py")

        loader = ExtensionLoader(os.path.dirname(decoder_file), "PJLink.Resources.Decoders")
        try:
            decoder_module = loader.load(decoder_file)
            decoder = decoder_module._decoder
        except Exception as e:
            import traceback as tb
            Env.logf(tb.format_exc())
        else:
            if not hasattr(decoder, "decode"): # must be defined in the file
                target = decoder[-1]
                if callable(target):
                    decoder = decoder[:-1]
                else:
                    target = namedtuple
                decoder = ObjectDecoder(*decoder, target=target)
            return decoder

    def encode(self, o, link):
        for encoder in self.encoders.values():
            enc = encoder.encode(o, link)
            if enc is not ObjectEncoder.Failed:
                return enc
        return o # fallback

    def load_encoders(self, path = None):
        import os

        if path is None:
            path = os.path.join(self._base_path, "Encoders")

        for f in os.listdir(path):
            if f.endswith(".py"):
                f, ext = os.path.splitext(os.path.basename(f))
                encoder = self.load_encoder(f, path = path)
                if encoder is not None:
                    self.encoders[f] = encoder

    def load_encoder(self, name, path = None):
        import os

        if os.path.isfile(name):
            encoder_file = name
        elif path is None:
            path = self._base_path
            encoder_file = os.path.join(path, "Encoders", name+".py")
        else:
            encoder_file = os.path.join(path, name+".py")

        loader = ExtensionLoader(os.path.dirname(encoder_file), "PJLink.Resources.Encoders")
        try:
            encoder_module = loader.load(encoder_file)
            encoder = encoder_module._encoder
        except:
            import traceback as tb
            Env.log(tb.format_exc())
        else:
            if not hasattr(encoder, "encode"): # must be defined in the file
                encoder = ObjectEncoder(*encoder)
            return encoder

    # def register_decoder(self, name, decoder, path = None, save = True):
    #     import os
    #
    #     if not isinstance(decoder, ObjectDecoder):
    #         decoder = ObjectDecoder(decoder)
    #
    #     if not isinstance(decoder, ObjectDecoder):
    #         raise TypeError("{}.register_decoder: got object '{}' but an 'ObjectDecoder' object is required".format(type(self).__name__, type(decoder).__name__))
    #     else:
    #         if save:
    #             if path is None:
    #                 path = self._decoder_path
    #             decoder_file = os.path.join(path, name.py)
    #             with open(decoder_file) as dec_f:
    #                 dec_f.write(decoder.serialize())
    #         self[name] = decoder

###############################################################################################
#                                                                                             #
#                                      ExtensionLoader                                          #
#                                                                                             #
###############################################################################################
# just a concrete implementation of a loader

import importlib.abc, os, importlib.util

class ExtensionLoader(importlib.abc.SourceLoader):
    """An ExtensionLoader creates a Loader object that can load a python module from a file path

    """

    def __init__(self, rootdir='', rootpkg = None):
        """
        :param rootdir: root directory to look for files off of
        :type rootdir: str
        :param rootpkg: root package to look for files off of
        :type rootpkg: str or None
        """
        self._dir=rootdir
        self._pkg = rootpkg
        super().__init__()

    def get_data(self, file):
        with open(file,'rb') as src:
            return src.read()

    def get_filename(self, fullname):
        if not os.path.exists(fullname):
            basename = os.path.splitext(fullname.split(".")[-1])[0]
            fullname = os.path.join(self._dir, basename+".py")
        if os.path.isdir(fullname):
            fullname = os.path.join(fullname, "__init__.py")
        return fullname

    def get_spec(self, file, pkg = None):
        base_name = os.path.splitext(os.path.basename(file))[0]
        package_origin = file
        if pkg is None:
            pkg = self._pkg
        if pkg is None:
            raise ImportError("{}: package name required to load file".format(type(self)))
        package_name = pkg + "." + base_name
        spec = importlib.util.spec_from_loader(
            package_name,
            self,
            origin=package_origin
        )
        return spec

    def load(self, file, pkg = None):
        """loads a file as a module with optional package name

        :param file:
        :type file: str
        :param pkg:
        :type pkg: str or None
        :return:
        :rtype: module
        """
        spec = self.get_spec(file, pkg)
        module = importlib.util.module_from_spec(spec)
        if module is None:
            module = importlib.util.module_from_spec(None)
        self.exec_module(module)
        return module


###############################################################################################
#                                                                                             #
#                                      ObjectHandler                                          #
#                                                                                             #
###############################################################################################
class ObjectHandler:
    """The utility of this is up for grabs... basically it'll one day just be a thing that makes it possible to drop a bunch of
    PyEvaluate calls on the Mathematica side... for now it's only partially implemented

    """

    __ref_table = {}
    __obj_counter = 1

    class Context:
        """A kludge for object lookup

        """

        __in_constructor = False

        def __init__(self, name, handler):
            self.__env   = handler.env
            self.__handler = handler
            self.__context_cache = handler.context_cache
            self.__name  = name
            self.__names = {}
            if not self.__in_constructor:
                raise NotImplemented

        @property
        def name(self):
            return self.__name

        def __getattr__(self, item):
            try:
                names = super().__getattribute__("__names")
            except AttributeError:
                names = {}
            try:
                return names[item]
            except KeyError:
                if item.endswith("__Context__"):
                    return self.get_subcontext(item[:-(len("__Context__")+1)])
                else:
                    try:
                        name = self.name
                    except AttributeError:
                        name = "UnnamedContext`"
                    raise NameError("Symbol '{}{}' not found".format(name, item))

        def __setattr__(self, key, value):
            if key.endswith("__Context__"):
                raise ValueError("Cannot assign to context {}".format(self.get_subcontext(key).name))
            names = self.__names
            names[key] = value

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
        def from_string(cls, full_name, handler):
            cache = handler.contexts

            try:
                cont = cache[full_name]
            except KeyError:
                bits = full_name.split("`")
                cont = cls.from_parts(bits, handler)
            return cont

        @classmethod
        def from_parts(cls, bits, handler):
            cache = handler.contexts

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
                    cont = cls(bits[0]+"`", handler)
                    cls.__in_constructor = False

                for b in bits[1:]:
                    cont = cont.get_subcontext(b)

            return cont

    def __init__(self, env):
        self.__env = env
        self.__objects = {}
        # self.__context_cache = {}

    @property
    def env(self):
        return self.__env
    # @property
    # def contexts(self):
    #     return self.__context_cache
    @property
    def objects(self):
        return self.__objects

    @staticmethod
    def clean_symbol_names(name):
        name = name.replace("$", "_")
        name = name.replace("`", "__Context__.")
        return name

    def exec_code(self, args):
        env = self.__env
        env["_PythonObjects"] = self.__objects
        if isinstance(args, str):
            args = [ args ]
        for chunk in args:
            # chunk = self.clean_symbol_names(chunk)
            exec(chunk, env, env)

    def _context_and_name(self, ref):
        if isinstance(ref, str):
            name = ref
        else:
            name = ref.args[0]

        env = self.__env
        bits = name.split("`")
        if len(bits)>1:
            # set the head context if necessary
            cont = self.Context.from_string(bits[0]+"`", env)
            env[bits[0]+"__Context__"] = cont
        name = self.clean_symbol_names(name)
        assign_bits = name.split(".")
        if len(assign_bits) == 1:
            context = env
        else:
            context = eval(".".join(assign_bits[:-2]), env, env)

        return context, name

    def _op(self, op, ref, *vals):
        val = self.get(ref)
        return val
    def _iop(self, op, ref, *vals):
        self.set(ref, self._op(op, ref, *vals))

    def _get_ref_id(self, ref):
        if isinstance(ref, int):
            return ref
        else:
            return ref.ref

    def remove(self, ref):
        # ctx, name = self._context_and_name(ref)
        rid = self._get_ref_id(ref)
        del self.__objects[rid]
        # if isinstance(ctx, dict):
        #     try:
        #         val = ctx[name]
        #         del self.__ref_table[val]
        #     except (KeyError, TypeError):
        #         pass
        #     del ctx[name]
        #
        # else:
        #     try:
        #         val = getattr(ctx, name)
        #         del self.__ref_table[val]
        #     except (AttributeError, KeyError, TypeError):
        #         pass
        #     delattr(ctx, name)

    def get(self, ref):
        rid = self._get_ref_id(ref)
        return self.__objects[rid]
        # ctx, name = self._context_and_name(ref)
        # if isinstance(ctx, dict):
        #     return ctx[name]
        # else:
        #     return getattr(ctx, name)

    def set(self, ref, val):
        rid = self._get_ref_id(ref)
        self.__objects[rid] = val
        # ctx, name = self._context_and_name(ref)
        # if isinstance(ctx, dict):
        #     ctx[name] = val
        # else:
        #     setattr(ctx, name, val)

    def new(self, val):
        ref_id = self.__obj_counter
        self.__obj_counter += 1
        self.set(ref_id, val)
        ref = PythonObject(ref_id, handler = self)
        # if isinstance(val, type):
        #
        #     name = val.__module__ + "." + val.__qualname__
        # else:
        #     tt = type(val)
        #     name = tt.__module__ + "." + tt.__qualname__ + "_{}".format(self.__obj_counter)
        #     self.__obj_counter += 1
        #
        # name = name.replace(".", "`")
        #
        # ref = MPackage.F(MPackage.PackageContext+"PythonObject", name)
        #
        # self.set(name, val)

            # self.__ref_table[id(val)] = ref
            # self.__ref_table[ref] = id(val)
            # # try:
            # #     self.__ref_table[id(val)] = ref
            # # except TypeError:
            # #     pass

        return ref

###############################################################################################
#                                              PythonObject                                   #
class PythonObject(namedtuple("PythonObject",   ["ref", "handler"])):
    """A lightweight reference to a variable which only exists to make Mathematica code a little cleaner"""
    __slots__ = ()

    def __new__(cls, ref, link = None, handler = None):
        if handler is None:
            handler = link.ObjectHandler
        return super().__new__(cls, (ref, handler))

    def __init__(self, *args, **kwargs):
        super().__init__()

    def get(self):
        return self.handler.get(self.ref)
    def set(self, val):
        return self.handler.set(self.ref, val)
    def remove(self):
        return self.handler.remove(self.ref)

    @property
    def expr(self):
        val = self.get()
        if isinstance(val, type):
            cls = val.__module__+"."+val.__qualname__
            add = val.__name__
        else:
            t = type(val)
            cls = t.__module__+"."+t.__qualname__
            add = id(val)
        return MPackage.F(MPackage.PackageContext+"PyObject", self.ref, cls, add)


    def __add__(self, amt):
        from operator import add
        return self.handler.ref(self.handler._op(add, self.ref, amt))
    def __sub__(self, amt):
        from operator import sub
        return self.handler.ref(self.handler._op(sub, self.ref, amt))
    def __mul__(self, amt):
        from operator import mul
        return self.handler.ref(self.handler._op(mul, self.ref, amt))
    def __call__(self, *args, **kwargs):
        return self.get()(*args, **kwargs)
    def __iadd__(self, amt):
        return self.handler._iop(self.ref, amt)
    def __imul__(self, amt):
        return self.handler.imul(self.ref, amt)
    def __getattr__(self, item):
        return self.handler.get()

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