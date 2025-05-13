#!/usr/bin/env python
"""
Custom test runner that ensures the compatibility layer is loaded
before unittest discovers and runs tests.
"""
import sys
import os
import unittest
import importlib
import argparse

# First, ensure medcat compatibility is set up
try:
    import medcat
except ImportError:
    try:
        import medcat2

        # Manually set up the redirection
        print("Setting up medcat compatibility layer...")

        # Create module for medcat
        import types
        medcat_module = types.ModuleType('medcat')
        sys.modules['medcat'] = medcat_module

        # Copy attributes
        for attr in dir(medcat2):
            if not attr.startswith('__'):
                setattr(medcat_module, attr, getattr(medcat2, attr))

        # Set up submodule proxies
        class SubmoduleProxy:
            def __init__(self, target_module_name):
                self.target_module_name = target_module_name
            
            def __getattr__(self, name):
                return getattr(importlib.import_module(self.target_module_name), name)

        # Add proxies for submodules
        for module_name in list(sys.modules.keys()):
            if module_name.startswith('medcat2.'):
                submodule_name = module_name.replace('medcat2.', 'medcat.', 1)
            elif module_name == 'medcat2':
                submodule_name = 'medcat'
            else:
                continue
            sys.modules[submodule_name] = SubmoduleProxy(module_name)  # type: ignore
    except ImportError:
        print("Warning: Neither medcat nor medcat2 could be imported")

# Now run the tests
if __name__ == '__main__':
    # Parse arguments to mimic unittest discover behavior
    parser = argparse.ArgumentParser(description='Run tests with compatibility layer')
    parser.add_argument('-s', '--start-directory', default='tests',
                        help='Directory to start discovery (default: tests)')
    parser.add_argument('-p', '--pattern', default='test*.py',
                        help='Pattern to match test files (default: test*.py)')
    parser.add_argument('-t', '--top-level-directory', default=None,
                        help='Top level directory of project (default: None)')
    parser.add_argument('--verbosity', '-v', type=int, default=2,
                        help='Verbosity level (default: 2)')

    args = parser.parse_args()

    # Ensure the start directory exists
    if not os.path.isdir(args.start_directory):
        print(f"Error: Start directory '{args.start_directory}' does not exist")
        sys.exit(1)

    # Get all tests using the specified parameters
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(
        start_dir=args.start_directory,
        pattern=args.pattern,
        top_level_dir=args.top_level_directory
    )

    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=args.verbosity)
    result = test_runner.run(test_suite)
    
    # Return non-zero exit code if tests failed
    sys.exit(not result.wasSuccessful())
