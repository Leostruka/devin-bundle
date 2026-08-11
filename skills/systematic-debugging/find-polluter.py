#!/usr/bin/env python3
"""Bisection script to find which test creates unwanted files/state.

Usage:
  python find-polluter.py <file_or_dir_to_check> <test_pattern>

Example:
  python find-polluter.py '.git' 'src/**/*.test.ts'
"""
import glob
import os
import subprocess
import sys


def find_test_files(pattern):
    """Return a sorted list of test files matching the pattern."""
    # Accept patterns with or without a leading ./
    pattern = pattern.lstrip("./").lstrip("\\")
    # Python glob with ** matches zero or more directories, so no collapse needed.
    files = glob.glob(pattern, recursive=True)
    # Also try with a leading ./ if the user wrote a relative pattern
    files += glob.glob("./" + pattern, recursive=True)
    # Filter to real files only and de-duplicate
    seen = set()
    result = []
    for f in files:
        if os.path.isfile(f):
            norm = os.path.normpath(f)
            if norm not in seen:
                seen.add(norm)
                result.append(norm)
    result.sort()
    return result


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <file_to_check> <test_pattern>")
        print(f"Example: {sys.argv[0]} '.git' 'src/**/*.test.ts'")
        sys.exit(1)

    pollution_check = sys.argv[1]
    test_pattern = sys.argv[2]

    print(f"Searching for test that creates: {pollution_check}")
    print(f"Test pattern: {test_pattern}")
    print()

    test_files = find_test_files(test_pattern)
    total = len(test_files)
    print(f"Found {total} test files")
    print()

    if not test_files:
        print("No test files found - check your pattern.")
        sys.exit(0)

    for count, test_file in enumerate(test_files, start=1):
        if os.path.exists(pollution_check):
            print(f"Pollution already exists before test {count}/{total}")
            print(f"   Skipping: {test_file}")
            continue

        print(f"[{count}/{total}] Testing: {test_file}")

        # Run the test; ignore failures to keep bisecting.
        subprocess.run(
            ["npm", "test", test_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if os.path.exists(pollution_check):
            print()
            print("FOUND POLLUTER!")
            print(f"   Test: {test_file}")
            print(f"   Created: {pollution_check}")
            print()
            print("Pollution details:")
            try:
                stat = os.stat(pollution_check)
                print(f"  mode={oct(stat.st_mode)}, size={stat.st_size}")
            except OSError:
                pass
            print()
            print("To investigate:")
            print(f"  npm test {test_file}    # Run just this test")
            print(f"  cat {test_file}         # Review test code")
            sys.exit(1)

    print()
    print("No polluter found - all tests clean!")
    sys.exit(0)


if __name__ == "__main__":
    main()
