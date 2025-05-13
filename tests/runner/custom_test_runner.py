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
import medcat
print("medcat?", medcat, ":", dir(medcat))
import medcat.cat
import medcat.vocab
import medcat.cdb
print("Loaded medcat")


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
