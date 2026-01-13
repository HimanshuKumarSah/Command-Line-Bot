import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("API_KEY"))

print("--- YOUR COMPATIBLE MODELS ---")
for model in client.models.list():
    if 'generateContent' in model.supported_actions:
        # We strip the 'models/' prefix to get the ID you need
        clean_id = model.name.replace("models/", "")
        print(f"ID: {clean_id}")