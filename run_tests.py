#!/usr/bin/env python3
"""
Script to run all tests with proper configuration.
"""
import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run all tests with multithreading and coverage."""
    print("Running comprehensive test suite...")
    
    # Add src to Python path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    # Run tests with multithreading
    cmd = [
        "python", "-m", "pytest", 
        "tests/", 
        "-n", "auto",  # Multithreaded
        "-v",  # Verbose
        "--tb=short",  # Short traceback
        "--disable-warnings",  # Disable warnings
        "--cov=src",  # Coverage
        "--cov-report=term-missing",  # Coverage report
        "--cov-report=html:htmlcov"  # HTML coverage report
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ pytest not found. Please install it with: pip install pytest pytest-xdist pytest-cov")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
