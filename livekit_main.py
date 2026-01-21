import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, cli, WorkerOptions
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import assemblyai, silero, cartesia, google
from tools import ALL_TOOLS
#from complexllm2 import MyCustomLLMStream

load_dotenv()
logger = logging.getLogger("voice-agent")

async def entrypoint(ctx: JobContext):
    logger.info(f"Starting agent in room: {ctx.room.name}")
    await ctx.connect()

    
    # Use Gemini LLM instead of OpenAI
    agent = Agent(
        instructions="""You are a friendly verification bot. Your job is to collect 4 pieces of information:
1. Full name
2. Phone number  
3. Email address
4. Company name

Ask for each piece of information one at a time in a friendly manner.
Once you have all 4 pieces of information, call the verify_and_save tool with all the details.
After calling verify_and_save, repeat all the information to the user and them if all the information is correct or not.
If the user says the information is not correct, ask the user for that information again.
Once the information is received, repeat that specific information again, and ask the user if the information is correct or not.
Once the user verifies the information is correct, call the verify_and_save tool and thank the user and call the end_call tool to end the conversation by saying an ending greeting.""",
        vad=silero.VAD.load(),
        stt=assemblyai.STT(),
        llm="google/gemini-2.5-flash", 
        tts="cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        tools=ALL_TOOLS,
    )
    
    session = AgentSession(
        allow_interruptions=True,
        min_interruption_duration=1.2,
        min_interruption_words=4,
        false_interruption_timeout=0.5,
        resume_false_interruption=True,
    )

    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")
    
    await session.start(agent, room=ctx.room)
    await session.say("Hello, I am your personal verification bot. May I know your full name?")
    

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))