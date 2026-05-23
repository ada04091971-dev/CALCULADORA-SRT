import unittest
from app_mega import balthazard

class TestBalthazard(unittest.TestCase):
    def test_empty_list(self):
        """Test with an empty list."""
        self.assertEqual(balthazard([]), 0.0)

    def test_single_value(self):
        """Test with a single value."""
        self.assertEqual(balthazard([40.0]), 40.0)
        self.assertEqual(balthazard([10]), 10.0)

    def test_zero_or_negative_values(self):
        """Test with zero or negative values which should be ignored."""
        self.assertEqual(balthazard([0]), 0.0)
        self.assertEqual(balthazard([-10, -20]), 0.0)
        self.assertEqual(balthazard([20, 0, -10]), 20.0)

    def test_two_values(self):
        """Test with two values to verify the formula."""
        # Formula: max + min * (100 - max) / 100
        # For 20 and 10: 20 + 10 * (80) / 100 = 20 + 8 = 28
        self.assertEqual(balthazard([20, 10]), 28.0)
        # Should be sorted properly, so order doesn't matter
        self.assertEqual(balthazard([10, 20]), 28.0)

    def test_multiple_unordered_values(self):
        """Test with multiple values to ensure proper sorting and calculation."""
        # For [50, 30, 20]:
        # 1. total = 50
        # 2. total = 50 + 30 * (100 - 50) / 100 = 50 + 15 = 65
        # 3. total = 65 + 20 * (100 - 65) / 100 = 65 + 7 = 72
        self.assertEqual(balthazard([20, 50, 30]), 72.0)

    def test_float_values_and_rounding(self):
        """Test with float values to ensure rounding to 2 decimal places."""
        # For [33.3, 22.2]:
        # total = 33.3 + 22.2 * (100 - 33.3) / 100
        # total = 33.3 + 22.2 * 0.667 = 33.3 + 14.8074 = 48.1074 -> 48.11
        self.assertEqual(balthazard([33.3, 22.2]), 48.11)

if __name__ == '__main__':
    unittest.main()
