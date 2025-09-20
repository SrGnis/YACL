#!/usr/bin/env python3
"""
Test runner script for YACL timeline functionality.
"""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run the timeline tests."""
    print("Running YACL Timeline Tests...")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--color=yes"
        ], cwd=project_dir, capture_output=False)
        
        if result.returncode == 0:
            print("\n" + "=" * 50)
            print("✅ All tests passed!")
        else:
            print("\n" + "=" * 50)
            print("❌ Some tests failed!")
            
        return result.returncode
        
    except FileNotFoundError:
        print("❌ pytest not found. Please install pytest:")
        print("pip install pytest")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def run_specific_test_module(module_name):
    """Run tests for a specific module."""
    print(f"Running tests for {module_name}...")
    print("=" * 50)
    
    project_dir = Path(__file__).parent
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            f"tests/{module_name}",
            "-v",
            "--tb=short",
            "--color=yes"
        ], cwd=project_dir, capture_output=False)
        
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test module
        module = sys.argv[1]
        exit_code = run_specific_test_module(module)
    else:
        # Run all tests
        exit_code = run_tests()
    
    sys.exit(exit_code)
