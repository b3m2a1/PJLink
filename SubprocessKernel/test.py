# import threading
#
# class hello:
#     say_hello = False
#
# def poll(cls):
#     import time
#
#     while not cls.say_hello:
#         pass
#
#     time.sleep(.1)
#     poll(cls)
#
# thd = threading.Thread(target=poll, args=(hello,))
#
# thd.start()
#
# import code
# code.interact(banner="", local=locals())

from PJLink.HelperClasses import *

__getattr__ = None

class MathematicaBlock:

    __TOTO = None
    __sym_dict = {}

    def __init__(self, update_globals = True):
        if self.__TOTO is not None:
            raise TypeError("MathematicaSyntax is a standalone object")
        self.__ns = None
        self.__getatt = None
        self.__ug = update_globals

    def __enter__(self):
        if MPackage.initialize_default():
            self.__sym_dict.update(dict(MPackage.symbol_list))
            self.__sym_dict.update((("Sym", MPackage)))

        if self.__ug:
            self.__glob = globals().copy()
            globals().update(self.__sym_dict)

        return self.__sym_dict

    def __exit__(self, exc_type, exc_val, exc_tb):

        if self.__ug:
            globals().clear()
            globals().update(self.__glob)
            self.__glob = None

# with MathematicaBlock():
#     print(Evaluate(Plus(M.a, M.b)))

def floop():
    import inspect
    return inspect.currentframe().f_back.f_locals