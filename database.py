import redis
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
import json

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client["chat_bot"]
collection = db["messages"]

def add_message(chat_id, role, text):
    collection.insert_one({
        "chat_id": chat_id,
        "role": role,
        "content": text,
        "timestamp": datetime.now()
    })

def get_full_history(chat_id):
    messages = list(collection.find({"chat_id": chat_id}).sort("timestamp", 1))
    return [f"{m['role']}: {m['content']}" for m in messages]
