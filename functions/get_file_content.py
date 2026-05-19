import os
from google.genai import types
def get_file_content_schema():
    schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="Gets contents of file and returns the last 1000 characters if there are more than 1000 characters",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="Name of file to get contents of relative to working directory (default is the working directory itself.) "
            )
        },
        required=["file_path"]
    ),
)   
    return schema_get_file_content

def get_file_content(working_directory, file_path):
    import os
    MAX_CHARS = 1000
    output_string = ""
    working_dir_abs = os.path.abspath(working_directory)
    target_path = os.path.join(working_dir_abs,file_path)

    target_path = os.path.normpath(target_path)
 
    if os.path.exists(target_path):
        if os.path.commonpath([working_dir_abs,target_path]) == working_dir_abs:
            if os.path.isfile(target_path) == True:
                with  open(target_path,'r') as file:
                    contents = file.read()
                    if len(contents) > MAX_CHARS:
                        contents = contents[-MAX_CHARS:]
                        contents += f'[...File "{file_path}" truncated to last {MAX_CHARS} characters]'
                        output_string += f'{os.path.basename(file.name)} truncated: True"'
                        output_string += contents

                    else:
                        output_string +=contents
                    
            else: 
                output_string += f'Error: File is a directory: "{file_path}"'
        else:
            output_string += (f'Error: Cannot read "{file_path}" as it is outside the permitted working directory')
    else:
        output_string += (f'Error: File not found or is not a regular file: "{file_path}"')
    return output_string