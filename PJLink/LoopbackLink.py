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

class NativeLoopbackLink(LoopbackLink, NativeLink):

    def __init__(self, init = None):

        if init is None:
            self.__errMsgOut = [ "" ]
            self._loadNativeLibrary()

            link = 0
            with self.__lock:
                link = self._call("LoopbackOpen", self.__errMsgOut)

            if self.__link == 0:
                if len(self.__errMsgOut) > 0:
                    err_msg = self.__errMsgOut[0]
                else:
                    err_msg = self.__CREATE_FAILED_MESSAGE
            raise MathLinkException("CreationFailed", err_msg)

        else:
            super.__init__(init)

    def setYieldFunction(self, meth):
        return False
    def _setYieldFunctionOn(self, target, meth):
        return False
    def addMessageHandler(self, meth):
        return False
    def _addMessageHandlerOn(self, target, meth):
        return False