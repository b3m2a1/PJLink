from PJLink.KernelLink import WrappedKernelLink
from PJLink.NativeLink import NativeLink
from PJLink.Reader import Reader
from PJLink.HelperClasses import MathematicaBlock as MathematicaBlock, LinkEnvironment as LinkEnvironment

import os

true_file = os.path.abspath(__file__)
main_dir = os.path.dirname(true_file)

class SubprocessKernel(WrappedKernelLink):
    """A little helper class that makes a WrappedKernelLink attached to a Mathematica FE

    """

    def __init__(self, init = None, debug_level = 0):
        super().__init__(NativeLink(init=init, debug_level=debug_level))
        self.__py_eval_link = None
        self.__reader = None
        self.setup()

    def setup(self):

        M = self.M

        kernel_init = M.Get(os.path.join(main_dir, "Kernel", "SubprocessKernel.wl"))

        kernel_config = M.CompoundExpression(
            M.Set(
                M.SubprocessKernel_SubprocessREPLSettings_("Links"),
                M.List(self.name)
            ),
            M.Set(
                M.SubprocessKernel_SubprocessREPLSettings_("InitializationMessage"),
                M.List(M.None_)
            )
        )

        # self.setLogging()

        self.evaluate(kernel_init)
        self.evaluate(kernel_config)

    def start(self):

        M = self.M

        kernel_open = M.SubprocessKernel_OpenSubprocessNotebook(StartREPL=False)
        self.evaluate(kernel_open)

    @property
    def evaluator(self):
        return self.__py_eval_link
    @property
    def evaluator_loop(self):
        return self.__reader

    def start_evaluator(self):

        M = self.M

        if isinstance(self.__py_eval_link, WrappedKernelLink):
            try:
                self.__py_eval_link.close()
            except:
                pass

        self.drain()
        extra_link = M.Set(M.SubprocessKernel_PyEvaluateLink_, M.LinkCreate())
        link_expr = self.evaluate(extra_link)

        self.evaluate(M.LinkActivate(M.SubprocessKernel_PyEvaluateLink_), wait=False)

        link = link_expr.args[0]
        link = WrappedKernelLink.from_link_name(link, mode="connect")
        link.connect()

        self.__py_eval_link = link
        self.__reader = Reader.create_reader(link, quit_on_link_end=True, start=True, always_poll=False)