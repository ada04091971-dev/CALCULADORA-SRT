import sys
from unittest.mock import MagicMock

# Mock streamlit and pandas to avoid running app code or requiring dependencies to execute fully during import
sys.modules['streamlit'] = MagicMock()
sys.modules['pandas'] = MagicMock()

from app_mega import balthazard

def test_balthazard_empty_list():
    assert balthazard([]) == 0.0

def test_balthazard_zeros_and_negatives():
    # Only values > 0 are considered
    assert balthazard([0, -10, -5]) == 0.0
    assert balthazard([40, 0, -5]) == 40.0

def test_balthazard_single_value():
    assert balthazard([40]) == 40.0

def test_balthazard_multiple_values():
    # 40 + (30 * (100 - 40) / 100) = 40 + 30 * 0.6 = 40 + 18 = 58
    assert balthazard([40, 30]) == 58.0

def test_balthazard_multiple_values_out_of_order():
    # Sorted first: [50, 10]
    # 50 + (10 * (100 - 50) / 100) = 50 + 10 * 0.5 = 55
    assert balthazard([10, 50]) == 55.0

def test_balthazard_with_100():
    # 100 + (20 * 0) = 100
    assert balthazard([100, 20]) == 100.0
    assert balthazard([20, 100]) == 100.0

def test_balthazard_floats_and_rounding():
    # [33.33, 20.5]
    # 33.33 + (20.5 * (100 - 33.33) / 100) = 33.33 + (20.5 * 0.6667) = 33.33 + 13.66735 = 46.99735
    # Rounded to 2 decimals -> 47.0
    assert balthazard([33.33, 20.5]) == 47.0

def test_balthazard_many_values():
    # [50, 30, 10]
    # 50 + 30*0.5 = 65
    # 65 + 10*(100-65)/100 = 65 + 3.5 = 68.5
    assert balthazard([10, 30, 50]) == 68.5
