import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key=os.getenv("API_KEY")

client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})

model_id = "gemini-2.5-flash-lite"

system_prompt = "You're a chatbot meant to give quick and short responses that are the length of 2 lines."
sys_temp = 0.4

def start_chat():
    transcript = []
    
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            break

        history_string = "\n".join(transcript)
        full_system_prompt = f"{system_prompt}\n\nPast Conversation: \n{history_string}"
        
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=full_system_prompt,
                    temperature=sys_temp,
                )
            )

            bot_response = response.text
            print(f"Bot: {bot_response}\n")

            transcript.append(f"User: {user_input}")
            transcript.append(f"Bot: {bot_response}")

            usage = response.usage_metadata

            print(f"Input token: {usage.prompt_token_count}")
            print(f"Output token: {usage.candidates_token_count}")
            print(f"Total tokens used: {usage.total_token_count}")

        except Exception as e:
            print(f"Error: {e}")


if __name__=="__main__":
    start_chat()
