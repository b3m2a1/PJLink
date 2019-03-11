"""All of the utilities that are used in testing the package. Presumably can be reused in other packages.

"""

import unittest, timeit, numpy as np, functools

TestCase = unittest.TestCase #just in case I want to change this up later

class DataGenerator:
    """Provides methods to generate relevant data for testing methods
    """

    @staticmethod
    def coords(n=50):
        return np.random.rand(n, 3)
    @staticmethod
    def multicoords(n=10, m=50):
        return np.random.rand(n, m, 3)
    @staticmethod
    def mats(n=1):
        return np.random.rand(n, 3, 3)
    @staticmethod
    def vecs(n=1):
        return np.random.rand(n, 3)

    @staticmethod
    def angles(n=50, r=(0, 360), use_rad=False):
        angles = np.random.uniform(*r, size=(n,))
        if use_rad:
            angles = np.rad2deg(angles)
        return angles
    @staticmethod
    def dists(n=50, minmax=(.5, 1.5)):
        return np.random.uniform(*minmax, size=(n,))
    @staticmethod
    def zmat(ncoords=15, use_rad=False):
        refs1 = np.sort(np.random.randint(0, ncoords, ncoords))
        refs2 = np.sort(np.random.randint(0, ncoords, ncoords))
        refs3 = np.sort(np.random.randint(0, ncoords, ncoords))
        ass = np.arange(0, ncoords)
        refs1 = np.amin(np.array((refs1, ass)), axis=0)
        refs2 = np.amin(np.array((refs2, ass)), axis=0)
        for i,rs in enumerate(zip(refs1, refs2)):
            r1, r2 = rs
            if i > 0 and r1 == r2:
                while r1 == r2:
                    r2 = (r2 + 1) % (i + 1)
                    # print(r1, r2, i)
                refs2[i] = r2
        refs3 = np.amin(np.array((refs3, ass)), axis=0)
        for i,rs in enumerate(zip(refs1, refs2, refs3)):
            r1, r2, r3 = rs
            if i > 1 and (r1 == r3 or r2 == r3):
                while (r1 == r3 or r2 == r3):
                    r3 = (r3 + 1) % (i + 1)
                refs3[i] = r3

        # raise Exception(np.array((refs1, refs1-refs2, refs1-refs3, refs2-refs3)))
        dists = DataGenerator.dists(ncoords)
        angles = DataGenerator.angles(ncoords, (0, 180), use_rad=use_rad)
        dihedrals = DataGenerator.angles(ncoords, (0, 360), use_rad=use_rad)

        return np.array([refs1+1, dists, refs2+1, angles, refs3+1, dihedrals ]).T
    @staticmethod
    def zmats(m=10, ncoords=15, use_rad=False):
        return np.array([DataGenerator.zmat(ncoords, use_rad) for i in range(m)])

class DebugTestClass(unittest.TestSuite):
    """The set of fast tests in the test suite"""
    pass
DebugTests = DebugTestClass()
class ValidationTestClass(unittest.TestSuite):
    """The set of slow tests in the test suite"""
    pass
ValidationTests = ValidationTestClass()
class TimingTestClass(unittest.TestSuite):
    """The set of fast tests in the test suite"""
    pass
TimingTests = TimingTestClass()

class timed:
    def __init__(self, **kw):
        self.kw = kw

    def get_time_list(self, time_elapsed):
        run_time = [0, 0, time_elapsed]
        if run_time[2] > 60:
            run_time[1] = int(run_time[2] / 60)
            run_time[2] = run_time[2] % 60
            if run_time[1] > 60:
                run_time[0] = int(run_time[1] / 60)
                run_time[1] = run_time[1] % 60
        return run_time

    def __call__(self, fn):
        @functools.wraps(fn)
        def timed_fn(*args, **kwargs):
            import sys
            func = fn
            val = None
            time_elapsed = timeit.timeit("val = func(*args, **kwargs)", globals = locals(), **self.kw)
            run_time = self.get_time_list(time_elapsed)
            run_time_averaged = self.get_time_list(
                time_elapsed / ( self.kw["number"] if "number" in self.kw else 1000000 )
            )
            print("{0.__name__}: took {1[0]}:{1[1]}:{1[2]} per loop with {2[0]}:{2[1]}:{2[2]} overall".format(func, run_time_averaged, run_time),
                  file=sys.stderr
                  )
            return val
        return timed_fn

def timingTest(fn):
    timer = timed()(fn)
    def Timing(*args, **kwargs):
        return timer(*args, **kwargs)
    return Timing
def timeitTest(**kwargs):
    timer = timed(**kwargs)
    def wrap(fn):
        inner_fn = timer(fn)
        def Timing(*args, **kwargs):
            return inner_fn(*args, **kwargs)
        return Timing
    return wrap

def debugTest(fn):
    def Debug(*args, **kwargs):
        return fn(*args, **kwargs)
    return Debug

def validationTest(fn):
    def Validation(*args, **kwargs):
        return fn(*args, **kwargs)
    return Validation

def TestRunner(**kw):
    if not "resultclass" in kw:
        kw["resultclass"] = unittest.TextTestResult
    if not "verbosity" in kw:
        kw["verbosity"] = 2
    return unittest.TextTestRunner(**kw)


_test_loader_map = {
    "Debug" : DebugTests,
    "Validation": ValidationTests,
    "Timing" : TimingTests
}
def load_tests(loader, tests, pattern):
    from itertools import chain
    tests = list(chain(*((t for t in suite) for suite in tests)))
    for test in tests:
        method = getattr(test, test._testMethodName)
        ttt = method.__name__
        if ttt not in _test_loader_map:
            ttt = "Debug"
        suite = _test_loader_map[ttt]
        suite.addTest(test)
    #
    # return _test_loader_map.values()

def LoadTests(start_dir):
    unittest.defaultTestLoader.discover(start_dir)
