"""These are the set of tests to the PyVPT package
Every type of tests should be its own module and should be tagged as either a FastTest, SlowTest, or TimingTest





"""



if __name__=="__main__":
    import os, sys
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(tests_dir))
    sys.path.insert(0, base_dir)

    from PyVPT.Tests import TestRunner, DebugTests, ValidationTests, TimingTests, LoadTests

    LoadTests(base_dir)

    quiet = False
    quiet = quiet or ("-q" in sys.argv)

    debug = True
    debug = debug or ("-D" in sys.argv)

    timing = False
    timing = timing or ("-T" in sys.argv)

    validate = False
    validate = validate or ("-V" in sys.argv)

    v_level = 1 if quiet else 2
    log_stream = open(os.path.join("test_results.txt"), "w") if ("-l" in sys.argv) else sys.stderr
    stderr1 = sys.stderr
    sys.stderr = log_stream
    runner = TestRunner(stream = log_stream, verbosity=v_level)

    debug_results= None
    if debug:
        print("\n"+"-"*70, file=log_stream)
        print("-"*70, file=log_stream)
        print("Running Debug Tests:"+"\n", file=log_stream)
        debug_results  = runner.run(DebugTests)

    validate_results= None
    if validate:
        print("\n"+"-"*70, file=log_stream)
        print("-"*70, file=log_stream)
        print("Running Validation Tests:"+"\n", file=log_stream)
        validate_results  = runner.run(ValidationTests)

    timing_results= None
    if timing:
        print("\n"+"-"*70, file=log_stream)
        print("-"*70, file=log_stream)
        print("Running Timing Tests:"+"\n", file=log_stream)
        timing_results  = runner.run(TimingTests)

    debug_status = (debug_results is None) or debug_results.wasSuccessful()
    timing_status = (timing_results is None) or timing_results.wasSuccessful()
    validate_status = (validate_results is None) or validate_results.wasSuccessful()
    overall_status = not (debug_status & timing_status & validate_status)

    sys.stderr = stderr1

    sys.exit(overall_status)



