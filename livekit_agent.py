import asyncio
import logging
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RoomIO,
    JobProcess,
    WorkerOptions,
    cli,
    inference,
)

from livekit.plugins import assemblyai
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")

class MyPhoneAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=("""You are a verification bot. Your job is to collect 4 pieces of information:
                1. Full name
                2. Phone number  
                3. Email address
                4. Company name

                Ask for each piece of information one at a time in a friendly manner.
                Once you have all 4 pieces of information, call the verify_and_save tool with all the details.
                After calling verify_and_save, thank the user and call the end_call tool to end the conversation."""),
            stt=assemblyai.STT(),
            llm="google/gemini-2.0-flash",
            tts="cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",

        )

async def entrypoint(ctx: JobContext):
    logger.info(f"Connecting to room: {ctx.room.name}")

    await ctx.connect()
    session = AgentSession()

    room_io = RoomIO(session, room=ctx.room)
    await room_io.start()

    agent = MyPhoneAgent()
    await session.start(agent=agent)

    await session.say("Hello.")

    logger.info("Agent is active, listening")
    
if __name__=="__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )