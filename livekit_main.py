import logging
import asyncio
import os
import json
from dotenv import load_dotenv
from datetime import datetime
from livekit import rtc
from livekit.agents import JobContext, cli, WorkerOptions, room_io, BackgroundAudioPlayer, BuiltinAudioClip, AudioConfig
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import assemblyai, google, elevenlabs, silero
from tools import ALL_TOOLS
from tools import set_conversation_tracker, summarize_conversation, format_conversation_for_summary
from customllm import agent_instructions

load_dotenv()
logger = logging.getLogger("voice-agent")

def setup_chat_logger(room_name, participant_id):
    """Create a logger for individual conversations"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    chat_log_file = f"logs/chat_{room_name}_{participant_id}_{timestamp}.json"
    return chat_log_file

class ConversationTracker:
    """Tracks and logs conversation between user and agent"""
    def __init__(self, log_file):
        self.log_file = log_file
        self.conversation = []
        self.start_time = datetime.now()
        self.summary = None
    
    def add_message(self, speaker, message):
        """Add a message to the conversation"""
        self.conversation.append({
            "timestamp": datetime.now().isoformat(),
            "speaker": speaker,
            "message":message
        })
        self._save_to_file()

    def set_summary(self, summary:str):
        self.summary = summary
        self._save_to_file()
    
    def _save_to_file(self):
        """Save conversation to JSON file"""
        os.makedirs(os.path.dirname(self.log_file) or '.', exist_ok=True)
        
        with open(self.log_file, 'w') as f:
            json.dump({
                "start_time": self.start_time.isoformat(),
                "duration": (datetime.now() - self.start_time).total_seconds(),
                "summary": self.summary,
                "messages": self.conversation
            }, f, indent=2)

async def entrypoint(ctx: JobContext):
    call_ended = False
    logger.info(f"Starting agent in room: {ctx.room.name}")
    await ctx.connect()

    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")

    log_file = setup_chat_logger(ctx.room.name, participant.identity)
    tracker = ConversationTracker(log_file)
    logger.info(f"Chat log will be saved to: {log_file}")

    set_conversation_tracker(tracker)

    agent = Agent(
        instructions=agent_instructions,
        vad=silero.VAD.load(),
        llm=google.realtime.RealtimeModel(
            voice="Puck",
            temperature=0.8,
            instructions=agent_instructions
        ),
        tts=elevenlabs.TTS(),
        tools=ALL_TOOLS,
        turn_detection="manual",
    )
    
    session = AgentSession(
        preemptive_generation=True,
        allow_interruptions=True,
        min_interruption_duration=1.2,
        min_interruption_words=4,
        false_interruption_timeout=0.5,
        resume_false_interruption=True,
    )

    # background_audio = BackgroundAudioPlayer(
    #     ambient_sound=AudioConfig(BuiltinAudioClip.OFFICE_AMBIENCE, volume=0.8),
    #     thinking_sound=[
    #         AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING, volume=0.8),
    #         AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING, volume=0.7),
    #     ],
    # )

    @session.on("tool_call")
    def on_tool_call(event):
        async def handle():
            if event.name == "end_call":
                await asyncio.sleep(0.5)

                conversation_text = format_conversation_for_summary(
                    tracker.conversation
                )

                summary = await summarize_conversation(
                    conversation_text=conversation_text,
                    llm=agent.llm
                )

                tracker.set_summary(summary)
                logger.info("Conversation summary saved")

        asyncio.create_task(handle())

    @session.on("user_transcript")
    def on_user_transcript(event):
        async def handle():
            """Fired when google Realtime finishes STT for a user utterance"""
            text = event.text.strip()
            if text:
                tracker.add_message("user", text)
                logger.info(f"[USER] {text}")
        asyncio.create_task(handle())

    @session.on("agent_transcript")
    def on_agent_transcript(event):
        async def handle():
            text = event.text.strip()
            if text:
                tracker.add_message("agent", text)
                logger.info(f"[AGENT] {text}")
        asyncio.create_task(handle())
    
    await session.start(
        agent, 
        room=ctx.room,
        room_options=room_io.RoomOptions(
            text_output=room_io.TextOutputOptions(
                sync_transcription=True
            ),
        ),
    )

    @session.on("tool_call")
    def on_tool_call(event):
        async def handle():
            nonlocal call_ended

            if event.name != "end_call":
                return

            if call_ended:
                return

            call_ended = True
            logger.info("End call detected – finalizing session")

            await session.stop_listening()

            conversation_text = format_conversation_for_summary(
                tracker.conversation
            )

            summary = await summarize_conversation(
                conversation_text=conversation_text,
                llm=agent.llm
            )

            tracker.set_summary(summary)
            logger.info("Conversation summary saved")

            await session.stop()

            await ctx.room.disconnect()

            await ctx.shutdown()

        asyncio.create_task(handle())
        async def force_exit():
            await asyncio.sleep(1.5)
            logger.warning("Forcing process exit due to lingering audio stream")
            os._exit(0)

        asyncio.create_task(force_exit()) 



    await asyncio.sleep(1.5)
    # await background_audio.start(room=ctx.room, agent_session=session)
    await session.say("Hello, I am your personal verification bot. May I know your full name?", allow_interruptions=False)
    logger.info(f"Chat log saved to: {log_file}")
    
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))