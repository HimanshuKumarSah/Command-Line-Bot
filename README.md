CLI based AI Chatbot.
Uses Gemini API Key for response generation.

Current Progress: Chat bot with database and redis server to store previous chats for context. Redis server is being used as a cache and mongo-db database is being used as full chat history along with chat log, timestamp and chat id. Functionality so if redis already has cache, database server doesn't need to be accessed. If no cache is present, summary is generated until 10 messages are present in the cache then the summary isn't sent with the system prompt to cut down on tokens being used.

Goals: 
---
- Automate a randomised chat-id and automatically load the chat based on the user logging in.
- Run database commands in a different thread for multi-threading performance and to not slow down the actual chatting process.


