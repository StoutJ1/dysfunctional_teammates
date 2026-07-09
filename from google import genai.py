from google import genai
from google.genai.types import HttpOptions
from google.genai import types
import os
from dotenv import load_dotenv
load_dotenv()
config = types.GenerateContentConfig(tools=[],system_instruction="test",)   
        
api_key = os.environ.get("GEMINI_API_KEY")
base_url_env = os.environ.get("BASE_URL_ENV")
client = genai.Client(api_key=api_key,http_options=HttpOptions(base_url=base_url_env))
messages = [types.Content(role="user",parts=[types.Part(text="Good morning"),])]

output = client.models.generate_content(model=f'models/{os.environ.get("MODEL")}',
                                                contents=messages,
                                                config=config)
print(output)        