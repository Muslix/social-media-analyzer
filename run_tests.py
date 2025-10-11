#!/usr/bin/env python3
"""
Test runner - ensures PYTHONPATH is set correctly
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now run tests
if __name__ == "__main__":
    import pytest
    exit_code = pytest.main(['-v', 'tests/'])
    sys.exit(exit_code)
