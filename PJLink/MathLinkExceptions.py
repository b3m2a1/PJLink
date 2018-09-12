

###############################################################################################
#                                                                                             #
#                                       MathLinkException                                     #
#                                                                                             #
###############################################################################################

from .MathLinkEnvironment import MathLinkEnvironment as Env

class MathLinkException(Exception):
    """ The exception thrown by methods in the MathLink and KernelLink interfaces when a link error occurs.
MathLinkExceptions are only for errors that involve the low-level link itself.
After you catch a MathLinkException, the first thing you should do is call clearError() to try to clear the error condition.
If you do not, then the next MathLink or KernelLink method you call will throw an exception again.

For programmers familiar with the C-language MathLink API, the throwing of a MathLinkException is equivalent to a C-language function returning a result code other than MLEOK.
 """

    Env = Env

    def __init__(self, err_no, err_msg = None, err_name = None):

        if isinstance(err_no, str):
            if err_name is None:
                err_name = err_no
            _err_no = err_no
            err_no = self.Env.getErrorInt(err_no)
            if err_no is None:
                raise ValueError("{}: Unknown MathLink error name {}".format(type(self).__name__, _err_no))

        if err_name is None:
            err_name = self.Env.getErrorName(err_no)

        if err_msg is None:
            Env.getErrorMessageText(err_no, False)

        self.msg = err_msg
        self.no = err_no
        self.name = err_name
        if err_name is not None and err_msg is not None:
            arg_template = "MathLinkException {0} ({1}): {2}"
        elif err_name is not None:
            arg_template = "MathLinkException {0} ({1})"
        elif err_msg is not None:
            arg_template = "MathLinkException {0}: {2}"
        else:
            arg_template = "MathLinkException {0}"

        super().__init__(arg_template.format(err_no, err_name, err_msg))

    # I need to actually implement this fuzz
    @staticmethod
    def lookupMessageText(err):
        return Env.getErrorMessageText(err)

    @classmethod
    def wrap_exception(cls, exc):
        msg = exc.args[0] if len(exc.args) > 0 else None
        err = cls("WrappedException", msg)
        err.error = exc
        return err

    @classmethod
    def raise_non_ml_error(cls, err_no, err_msg = None):
        if err_no > cls.Env.getErrorInt("NonMLError"):
            raise cls(err_no, err_msg)

