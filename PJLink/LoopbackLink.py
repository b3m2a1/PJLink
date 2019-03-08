from .MathLink import MathLink
from .NativeLink import NativeLink
from .MathLinkExceptions import *

class LoopbackLink(MathLink):
    """LoopbackLink is the link interface that represents a special type of link
known as a loopback link. Loopback links are links that have both ends
connected to the same program, much like a FIFO queue. Loopback links are useful
as temporary holders of expressions that are being moved between links, or as
scratchpads on which expressions can be built up and then transferred to other
links in a single call.
Much of the utility of loopback links to users of the C-language MathLink API
is obviated by J/Link's Expr class, which provides many of the same features
in a more accessible way (Expr uses loopback links heavily in its implementation).

Objects of type LoopbackLink are created by the createLoopbackLink method in the
MathLinkFactory class.

LoopbackLink has no methods; it is simply a type that marks certain links as having
special properties.
"""
    pass

class NativeLoopbackLink(NativeLink, LoopbackLink):

    def __init__(self, init = None):

        if init is None:

            import os, re, threading
            from collections import deque
            self._init = init

            lock = threading.RLock()
            errMsgOut = [ "" ]

            with lock:
                cap, link = self._call("LoopbackOpen", errMsgOut)

            super().__init__((cap, link), errMsgOut = errMsgOut)

            if self._link == 0:
                if len(self._errMsgOut) > 0:
                    err_msg = self.__errMsgOut[0]
                else:
                    err_msg = self.__CREATE_FAILED_MESSAGE
                raise MathLinkException("CreationFailed", err_msg)

        else:
            super().__init__(init)

    def _setUseNumPy(self, flag):
        self._USE_NUMPY = flag
        return flag
    def _getUseNumPy(self):
        return self.use_numpy
    def setYieldFunction(self, meth):
        return False
    def _setYieldFunctionOn(self, target, meth):
        return False
    def addMessageHandler(self, meth):
        return False
    def _addMessageHandlerOn(self, target, meth):
        return False



class NativeScratchPadLink(NativeLoopbackLink):

    def __init__(self, parent, init=None):
        super().__init__(init)
        self.parent = parent
        try:
            self._kernel = parent._kernel
        except AttributeError:
            self._kernel = parent

    def _putMLExpr(self, call, stack = None, tmp = False):
        NativeLink._putMLExpr(self, call, stack = None, use_tmp = False)

    def _getUseNumPy(self):
        return self.parent.use_numpy