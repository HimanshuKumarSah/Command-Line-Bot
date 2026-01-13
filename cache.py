import redis
import os
import json
from dotenv import load_dotenv

load_dotenv()

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=os.getenv("REDIS_PORT", 6379),
    decode_responses=True
)

def add_to_cache(chat_id, role, content):
    key = f"chat_cache:{chat_id}"
    data=json.dumps({"role": role, "content": content})

    r.rpush(key,data)
    r.ltrim(key, -10, -1)

def get_recent_cache(chat_id):
    key = f"chat_cache:{chat_id}"
    raw_data = r.lrange(key, 0, -1)
    return [json.loads(msg) for msg in raw_data]

def clear_cache(chat_id):
    r.delete(f"chat_cache:{chat_id}")