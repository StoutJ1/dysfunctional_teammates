from google.genai import types
from get_files_info import get_file_info_schema
available_functions = types.Tool(
    function_declarations=[get_file_info_schema],
)