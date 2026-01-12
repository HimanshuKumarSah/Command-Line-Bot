import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key=os.getenv("API_KEY")

client = genai.Client(api_key=api_key)

model_id = "gemini-2.5-flash"

system_prompt = "You're a chatbot meant to give quick and 2 lines short responses."
sys_temp = 0.4

def start_chat():
    chat = client.chats.create(
        model=model_id,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=sys_temp,
        )
    )
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            break

        try:
            stream = True
            response = chat.send_message(user_input)
            usage = response.usage_metadata
            print(f"Bot:, {response.text}\n")

            print(f"Input token: {usage.prompt_token_count}")
            print(f"Output token: {usage.completion_token_count}")
            print(f"Total tokens used: {usage.total_token_count}")

        except Exception as e:
            print(f"Error: {e}")


if __name__=="__main__":
    start_chat()
