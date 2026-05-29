import pytest
from unittest.mock import patch

# Mock os.path.exists first so Streamlit doesn't die reading its config
original_exists = __import__('os').path.exists

def custom_exists(path):
    if "calculadora_final_srt.xlsx" in str(path):
        return False
    return original_exists(path)

# Custom exception to mock st.stop()
class StreamlitStopException(Exception):
    pass

def test_abrir_excel_error_path():
    import sys
    # Load app_mega without patches to avoid breaking global stream_lit state
    if 'app_mega' in sys.modules:
        del sys.modules['app_mega']

    import app_mega

    if hasattr(app_mega.abrir_excel, 'clear'):
        app_mega.abrir_excel.clear()

    with patch('streamlit.stop', side_effect=StreamlitStopException) as mock_stop, \
         patch('streamlit.error') as mock_error, \
         patch('os.path.exists', side_effect=custom_exists) as mock_exists:

        with pytest.raises(StreamlitStopException):
            app_mega.abrir_excel()

        mock_error.assert_called_once_with("No se encontró el archivo 'calculadora_final_srt.xlsx' en la carpeta de GitHub.")
        mock_stop.assert_called_once()
