import csv
import logging
import asyncio
import os
import sys
from datetime import datetime
from livekit.agents import function_tool, RunContext, get_job_context, JobContext
from livekit import rtc, api
from livekit.api import DeleteRoomRequest

logger = logging.getLogger("voice-agent")

_conversation_tracker = None

def set_conversation_tracker(tracker):
    """Set the global conversation tracker"""
    global _conversation_tracker
    _conversation_tracker = tracker

@function_tool
async def verify_and_save(
    ctx: RunContext,
    name: str,
    phone: str,
    email: str,
    company: str
) -> str:
    """Verify user details and save them to the database.
    Args:
        name: Full name of the user
        phone: Phone number
        email: Email address
        company: Company name"""
    
    logger.info(f"Verifying and saving: {name}, {phone}, {email}, {company}")

    if _conversation_tracker:
        _conversation_tracker.add_message("user", f"name: {name}, phone: {phone}, email: {email}, company:{company}" )
    
    csv_file = "user_data.csv"
    
    try:
        # Read existing data
        existing_data = []
        user_found = False
        user_index = -1
        
        normalized_data = []
        for row in existing_data:
            normalized_data.append({
                'Name': row.get('Name') or row.get('name'),
                'Phone': row.get('Phone') or row.get('phone'),
                'Email': row.get('Email') or row.get('email'),
                'Company': row.get('Company') or row.get('company'),
                'LastUpdated': row.get('LastUpdated') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        existing_data = normalized_data

        # Check if file exists
        if os.path.isfile(csv_file):
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    existing_data.append(row)
                    # Match by phone number (unique identifier)
                    if row.get('Phone') == phone:
                        user_found = True
                        user_index = idx
        
        # Prepare new data
        new_entry = {
            'Name': name,
            'Phone': phone,
            'Email': email,
            'Company': company,
            'LastUpdated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if user_found:
            # Check if there are any changes
            old_entry = existing_data[user_index]
            changes = []
            
            if old_entry.get('Name') != name:
                changes.append(f"Name: {old_entry.get('Name')} → {name}")
            if old_entry.get('Email') != email:
                changes.append(f"Email: {old_entry.get('Email')} → {email}")
            if old_entry.get('Company') != company:
                changes.append(f"Company: {old_entry.get('Company')} → {company}")
            
            if changes:
                # Update the existing entry
                existing_data[user_index] = new_entry
                logger.info(f"Updated user {name}. Changes: {', '.join(changes)}")
                message = f"Thank you {name}! I've updated your information: {', '.join(changes)}."
            else:
                logger.info(f"No changes detected for {name}")
                message = f"Thank you {name}! Your information is already up to date."
        else:
            # Add new user
            existing_data.append(new_entry)
            logger.info(f"Added new user: {name}")
            message = f"Thank you {name}! Your information has been saved."
        
        # Write back to CSV
        fieldnames = ['Name', 'Phone', 'Email', 'Company', 'LastUpdated']
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_data)
        
        logger.info(f"✓ Successfully saved to {os.path.abspath(csv_file)}")

        if _conversation_tracker:
            _conversation_tracker.add_message("agent", message)

        return message
        
    except Exception as e:
        logger.error(f"Failed to verify and save: {e}")
        return "I apologize, there was an error processing your information. Please try again."

@function_tool
async def end_call(ctx: RunContext) -> str:
    """End the phone call and exit the program."""
    logger.info("Agent is hanging up")

    if _conversation_tracker:
        _conversation_tracker.add_message("agent", "Call ended, Goodbye!")

    return "Call ended"

SUMMARY_PROMPT = """
    Summarize the following conversation in 2–3 sentences.
    Focus on the user's provided details and the final outcome.

    Conversation:
    {conversation}"""
async def summarize_conversation(conversation_text: str, llm) -> str:
    """System tool to summarize a completed conversation.
    This is NOT exposed to the LLM as a callable tool.
    """
    result = await llm.complete(
        SUMMARY_PROMPT.format(conversation=conversation_text)
    )
    return result.text.strip()

def format_conversation_for_summary(message):
    """
    messages: list of conversation entries from ConversationTracker
    """
    return "\n".join(
        f"{m['speaker'].upper()}: {m['message']}"
        for m in message
    )
    

ALL_TOOLS = [verify_and_save, end_call]