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
            instructions=("""You are a helpful voice AI assistant.
            You eagerly assist users with their questions by providing information from your database. You
            should answer the queires of a user based on the context that is provided and your answers should not be complicated."""),
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