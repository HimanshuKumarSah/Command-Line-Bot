CLI based AI Chatbot.
Uses Gemini API Key for response generation.

Goals: To optimize temperature and tokens to find a middle ground of good response with as less token usage as possible.

Current Progress: Basic chatbot working with per day rate limit of 20 questions to ask and answer.

Outputs based on Different Temperatures:
---

sys_temp=0.1 <br>
Input: What is delhi <br>
Output: Delhi is the capital city of India, a vast metropolis that serves as the seat of government.
It's a city steeped in history, with ancient monuments and a vibrant modern culture.  
Input tokens: 26  
Total tokens: 64


sys_temp=0.2 <br>
Input: What is delhi <br>
Output: Delhi is the capital city of India, a sprawling metropolis with a rich history and diverse culture.
It's known for its ancient monuments, bustling markets, and vibrant street life.  
Input tokens: 26  
Total tokens: 63

sys_temp=0.3 <br>
Input: What is delhi <br>
Output:Delhi is the capital city of India, a vast metropolis that serves as a major political, cultural, and commercial hub.
It's known for its rich history, diverse population, and iconic landmarks like the Red Fort and India Gate.  
Input tokens: 26  
Total tokens: 74

sys_temp=0.4 <br>
Input: What is delhi <br>
Output: Delhi is the capital city of India, a vast metropolis with a rich history. It's a bustling hub of culture, commerce, and government.  
Input tokens: 26  
Total tokens: 56  

sys_temp=0.5 <br>
Input: What is delhi <br>
Output: Delhi is a sprawling metropolis in India, serving as its capital territory. It's a vibrant city with a rich history and a blend of ancient monuments and modern infrastructure.  
Input tokens: 26  
Total tokens: 60  

sys_temp=0.6 <br>
Input: What is delhi <br>
Output: Delhi is the capital city of India, a vibrant metropolis with a rich history.
It's known for its diverse culture, historical monuments, and bustling markets.  
Input tokens: 26  
Total tokens: 59  

sys_temp=0.7 <br>
Input: What is delhi <br>
Output: Delhi is the capital city of India and a vast metropolitan area. It's known for its rich history, diverse culture, and bustling urban life.  
Input tokens: 26  
Total tokens: 56  

sys_temp=0.8 <br>
Input: What is delhi <br>
Output: Delhi is the capital of India, a sprawling metropolis with a rich history.
It's a vibrant city that blends ancient monuments with modern infrastructure.  
Input tokens: 26  
Total tokens: 56  

sys_temp=0.9 <br>
Input: What is delhi <br>
Output: Delhi is the capital city of India. It's a vast metropolitan area with a rich history and a diverse population.  
Input tokens: 26  
Total tokens: 50  

sys_temp=1.0 <br>
Input: What is delhi <br>
Output: Delhi is the capital of India, a vast metropolis with a rich history and diverse culture. It's a bustling hub of government, commerce, and vibrant street life.  
Input tokens: 26  
Total tokens: 60  

sys_temp=2.0 <br>
Input: What is delhi <br>
Output: Delhi is a large city and a Union Territory in northern India.
It's the capital territory of India and is a massive metropolitan area.  
Input tokens: 26  
Total tokensL 50
