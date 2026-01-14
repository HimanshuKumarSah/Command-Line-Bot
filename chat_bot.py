import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key=os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})

model_id = "gemini-2.5-flash"

sys_temp = 0.4

def generate_summary(history_list):
    if not history_list:
        return "No previous conversations."
    
    history_text = "\n".join(history_list)
    prompt = f"Summarize the following conversation history. \n{history_text}"

    try:
        response = client.models.generate_content(
                model=model_id,
                contents=prompt
            )
        return response.text
    
    except Exception as e:
        return f"Summary unavailable: {e}"

def get_response(user_input, system_instruction, sys_temp):
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=sys_temp,
            )
        )
        return response.text, response.usage_metadata

    except Exception as e:
        return f"Error: {e}", None

