import os
from dotenv import load_dotenv

load_dotenv() # Loads variables from .env into environment variables

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Gemini API Key not found. Make sure it's set in your .env file or environment variables.")

# Now use the api_key variable to configure the Gemini client
# genai.configure(api_key=api_key)
