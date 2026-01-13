import database  as db
import chat_bot as ai
import cache as rc
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=2)

def background_log(chat_id, role, content):
    try:
        db.add_message(chat_id, role, content)
        rc.add_to_cache(chat_id, role, content)
    except Exception as e:
        print(f"Failed to save data (background process): {e}")

def start_app():
    chat_id = input("Enter your user ID: ").strip()
    recent_content = rc.get_recent_cache(chat_id)
    if recent_content:
        memory_snapshot = "Recent session active."
    else:
        print("No recent session found. Generating memory snapshot.")
        past_history = db.get_full_history(chat_id)

        if past_history:    
            memory_snapshot = ai.generate_summary(past_history)
            for message in past_history[-10:]:
                role, content = message.split(": ", 1)
                rc.add_to_cache(chat_id, role, content)

            recent_content = rc.get_recent_cache(chat_id)
        else:
            memory_snapshot = "No previous conversations."
            recent_content = []

    print(f"Memory: {memory_snapshot}\n")

    system_prompt = "You're a chatbot meant to give quick and short responses that are the length of 2 lines."


    while True:
        user_input = input("\nUser: ").strip()
        if user_input.lower() in ["exit", "quit", "bye"]:
            executor.shutdown(wait=True)
            break
        
        # history_string = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_content])
        # full_system_prompt = (
        #     f"{system_prompt}\n\n"
        #     f"Summary of past sessions: {memory_snapshot}\n\n"
        #     f"Current session transcript: \n{history_string}"
        # )

        history_string = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_content])

        if len(recent_content) >= 10:
            active_summary = ""
            context_label = "Full window reached for context."

        else:
            active_summary = f"Summary of past sessions: {memory_snapshot}\n\n"
            context_label = "Using full history for context."
        full_system_prompt = (
            f"{system_prompt}\n\n" 
            f"{active_summary}"
            f"{context_label}\n"
            f"{history_string}"
        )

        try:
            bot_text, usage = ai.get_response(user_input, full_system_prompt, ai.sys_temp)
            print(f"Bot: {bot_text}\n")

            executor.submit(background_log, chat_id, "user", user_input)
            executor.submit(background_log, chat_id, "bot", bot_text)

            recent_content = rc.get_recent_cache(chat_id)

            if usage:
                print(f"Input token: {usage.prompt_token_count}")
                # print(f"Output token: {usage.completion_token_count}")
                print(f"Total tokens used: {usage.total_token_count}")
        
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    start_app()