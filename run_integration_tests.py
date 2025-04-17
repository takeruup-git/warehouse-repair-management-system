#!/usr/bin/env python3
import os
import sys
import pytest

def main():
    """Run integration tests for the warehouse repair management system."""
    print("Running integration tests...")
    
    # Create uploads directory if it doesn't exist
    os.makedirs('tests/uploads/forklift', exist_ok=True)
    os.makedirs('tests/uploads/facility', exist_ok=True)
    
    # Run the tests
    result = pytest.main(['-xvs', 'tests/integration'])
    
    if result == 0:
        print("\n✅ All integration tests passed!")
        return 0
    else:
        print("\n❌ Some integration tests failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())