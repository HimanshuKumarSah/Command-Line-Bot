import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, cli, WorkerOptions
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import assemblyai, silero, cartesia, google
from tools import ALL_TOOLS
from complexllm2 import MyCustomLLM

load_dotenv()
logger = logging.getLogger("voice-agent")

async def entrypoint(ctx: JobContext):
    logger.info(f"Starting agent in room: {ctx.room.name}")
    await ctx.connect()

    my_model = MyCustomLLM()
    
    # Use Gemini LLM instead of OpenAI
    agent = Agent(
        instructions="""You are a verification bot. Your job is to collect 4 pieces of information:
1. Full name
2. Phone number  
3. Email address
4. Company name

Ask for each piece of information one at a time in a friendly manner.
Once you have all 4 pieces of information, call the verify_and_save tool with all the details.
After calling verify_and_save, thank the user and call the end_call tool to end the conversation.""",
        vad=silero.VAD.load(),
        stt=assemblyai.STT(),
        llm=my_model, 
        tts="cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        tools=ALL_TOOLS,
    )
    
    session = AgentSession(
        allow_interruptions=True,
        min_interruption_duration=1.0,
        min_interruption_words=2,
        false_interruption_timeout=3.0,
        resume_false_interruption=True,
    )
    
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")
    
    await session.start(agent, room=ctx.room)
    await session.say("Hello, I am your personal verification bot. May I know your full name?")

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))