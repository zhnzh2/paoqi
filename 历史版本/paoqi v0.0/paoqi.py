def add(a, b):
    """Add two numbers"""
    return a + b

def subtract(a, b):
    """Subtract two numbers"""
    return a - b

def test_arithmetic():
    """Test arithmetic operations"""
    assert add(5, 3) == 8
    assert add(-1, 1) == 0
    assert subtract(10, 4) == 6
    assert subtract(0, 5) == -5
    print("All tests passed!")

if __name__ == "__main__":
    test_arithmetic()