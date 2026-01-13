CLI based AI Chatbot.
Uses Gemini API Key for response generation.

Current Progress: Chat bot with database and redis server to store previous chats for context. Redis server is being used as a cache and mongo-db database is being used as full chat history along with chat log, timestamp and chat id.

Goals: 
---
- Automate a randomised chat-id and automatically load the chat based on the user logging in.
- Run database commands in a different thread for multi-threading performance and to not slow down the actual chatting process.


