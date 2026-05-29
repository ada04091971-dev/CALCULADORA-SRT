import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import streamlit as st

import app_mega

def test_balthazard_empty():
    assert app_mega.balthazard([]) == 0.0

def test_balthazard_single_item():
    assert app_mega.balthazard([20]) == 20.0

def test_balthazard_multiple_items():
    # 20 + 10 * (100-20)/100 = 20 + 8 = 28.0
    assert app_mega.balthazard([20, 10]) == 28.0

def test_balthazard_three_items():
    # 50 + 20*(50/100) = 60
    # 60 + 10*(40/100) = 64.0
    assert app_mega.balthazard([50, 20, 10]) == 64.0

def test_balthazard_ignore_negatives_and_zeros():
    assert app_mega.balthazard([20, 0, -5, 10]) == 28.0

@patch('app_mega.os.path.exists')
@patch('app_mega.pd.ExcelFile')
def test_abrir_excel_success(mock_excel_file, mock_exists):
    app_mega.abrir_excel.clear() # Clear Streamlit cache
    mock_exists.return_value = True
    mock_excel_instance = MagicMock()
    mock_excel_file.return_value = mock_excel_instance

    result = app_mega.abrir_excel()

    mock_exists.assert_called_once_with("calculadora_final_srt.xlsx")
    mock_excel_file.assert_called_once_with("calculadora_final_srt.xlsx")
    assert result == mock_excel_instance

@patch('app_mega.os.path.exists')
@patch('app_mega.st.error')
@patch('app_mega.st.stop')
def test_abrir_excel_file_not_found(mock_stop, mock_error, mock_exists):
    app_mega.abrir_excel.clear() # Clear Streamlit cache
    mock_exists.return_value = False
    mock_stop.side_effect = Exception("Stop called") # Stop raises an exception in streamlit

    with pytest.raises(Exception, match="Stop called"):
        app_mega.abrir_excel()

    mock_exists.assert_called_once_with("calculadora_final_srt.xlsx")
    mock_error.assert_called_once_with("No se encontró el archivo 'calculadora_final_srt.xlsx' en la carpeta de GitHub.")
    mock_stop.assert_called_once()
