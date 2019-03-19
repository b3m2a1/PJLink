from .TestUtils import *

class CompilationTest(TestCase):

    @debugTest
    def importLib(self):
        import PJLink.PJLinkNativeLibrary.lib as lib
        import types
        self.assertIsInstance(lib.Open, types.FunctionType)