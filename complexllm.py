import uuid
import json
import re
import asyncio
from livekit.agents import llm

class MyCustomLLMStream(llm.LLMStream):
    def __init__(self, llm_instance, chat_ctx, fnc_ctx=None, tools=None, conn_options=None):

        self._fnc_ctx = fnc_ctx
        self._sent = False
        self._llm_instance = llm_instance

        super().__init__(
            llm=llm_instance,
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options or llm.LLMConnOptions()
        )

    async def _run(self):
        print(f"ChatContext type: {type(self.chat_ctx)}")
        print(f"ChatContext attributes: {dir(self.chat_ctx)}")

        """Process that conversation and generte appropriate response"""
        if self._sent:
            return
        
        self._sent = True

        # Check if the last message is a tool result
        messages = list(self.chat_ctx.messages) if hasattr(self.chat_ctx, 'messages') else []
        last_msg = messages[-1] if messages else None
        if last_msg and last_msg.role == "tool":
            #Handle tool result
            await self._handle_tool_result(last_msg)
            return
        
        # Get the last user message
        try:
            user_input = "" 
            if last_msg and last_msg.role == "user":
                content = last_msg.content
                if isinstance(content, list):
                    user_input = "".join([str(c) for c in content])
                else:
                    user_input = str(content)

        except:
            user_input = ""

        # Extract collected information from conversation history
        collected_info = self._extract_info_from_history()

        # Check for goodbye
        if any(word in user_input.lower() for word in ["bye", "goodbye", "end", "that's all", "thanks"]):
            chunk = llm.ChatChunk(
                id=str(uuid.uuid4()),
                delta=llm.ChoiceDelta(
                    role="assistant",
                    content="Goodbye! Have a great day."
                )
            )
            self._event_ch.send_nowait(chunk)

            # Call end_call tool
            await asyncio.sleep(0.1)
            end_chunk=llm.ChatChunk(
                id=str(uuid.uuid4()),
                delta=llm.ChoiceDelta(
                    role="assistant",
                    tool_calls=[llm.FunctionToolCall(
                        id="tc_end_" + str(uuid.uuid4())[:8],
                        name="end_call",
                        arguments="{}"
                    )]
                )
            )
            self._event_ch.send_nowait(end_chunk)
            return
        
        # Check for all required information
        missing_fields = []
        if not collected_info.get('name'):
            missing_fields.append('name')
        if not collected_info.get('phone'):
            missing_fields.append('phone number')
        if not collected_info.get('email'):
            missing_fields.append('email')
        if not collected_info.get('company'):
            missing_fields.append('company name')

        # If we have all the info, call verify_and_save
        if not missing_fields:
            # First send a text response
            text_chunk = llm.ChatChunk(
                id=str(uuid.uuid4()),
                delta=llm.ChoiceDelta(
                    role="assistant",
                    content="Thank you! Let me verify and save your information."
                )
            )
            self._event_ch.send_nowait(text_chunk)

            # Then call the tool
            await asyncio.sleep(0.1)
            tool_args = json.dumps(collected_info)
            tool_chunk = llm.ChatChunk(
                id=str(uuid.uuid4()),
                delta=llm.ChoiceDelta(
                    role="assistant",
                    tool_calls=[llm.FunctionToolCall(
                        id="tc_verify_" + str(uuid.uuid4())[:8],
                        name="verify_and_save",
                        arguments=tool_args
                    )]
                )
            )
            self._event_ch.send_nowait(tool_chunk)
            return
        
        # Generate response asking for missing information
        response_text = self._generate_response(user_input, collected_info, missing_fields)

        chunk = llm.ChatChunk(
            id=str(uuid.uuid4()),
            delta=llm.ChoiceDelta(role="assistant", content=response_text)
        )
        self._event_ch.send_nowait(chunk)

    async def _handle_tool_result(self, tool_msg):
        """Hande the result from verify_and_save tool"""

        try:
            content = tool_msg.content
            if isinstance(content, list):
                result_str = "".join([str(c) for c in content])
            else:
                result_str = str(content)

            # The tool returns just "Updated" as a string
            if "UPDATED" in result_str.upper():
                # Get the collected info from history
                collected_info = self._extract_info_from_history()

                info_text = f"Perfect! I've saved your information. Name: {collected_info.get('name')}, Phone: {collected_info.get('phone')}, Email: {collected_info.get('email')}, Company: {collected_info.get('company')}. Thank you for your time!"

                chunk = llm.ChatChunk(
                    id=str(uuid.uuid4()),
                    delta=llm.ChoiceDelta(
                        role="assistant",
                        content=info_text
                    )
                )
                self._event_ch.send_nowait(chunk)

                # Call end_call after a brief delay
                await asyncio.sleep(0.1)
                end_chunk = llm.ChatChunk(
                    id=str(uuid.uuid4()),
                    delta=llm.ChoiceDelta(
                        role="assistant",
                        tool_calls=[llm.FunctionToolCall(
                            id="tc_end_" + str(uuid.uuid4())[:8],
                            name="end_call",
                            arguments="{}"
                        )]
                    )
                )
                self._event_ch.send_nowait(end_chunk)

            elif "MATCH" in result_str.upper():
                chunk = llm.ChatChunk(
                    id=str(uuid.uuid4()),
                    delta=llm.ChoiceDelta(
                        role="assistant",
                        content="Thank you! Your information has been verified. Goodbye!"
                    )
                )
                self._event_ch.send_nowait(chunk)

                
                await asyncio.sleep(0.1)
                end_chunk = llm.ChatChunk(
                    id=str(uuid.uuid4()),
                    delta=llm.ChoiceDelta(
                        role="assistant",
                        tool_calls=[llm.FunctionToolCall(
                            id="tc_end_" + str(uuid.uuid4())[:8],
                            name="end_call",
                            arguments="{}"
                        )]
                    )
                )
                self._event_ch.send_nowait(end_chunk)
            else:
                chunk = llm.ChatChunk(
                    id=str(uuid.uuid4()),
                    delta=llm.ChoiceDelta(
                        role="assistant",
                        content="There was an issue processing your information. Please try again."
                    )
                )
                self._event_ch.send_nowait(chunk)
        except Exception as e:
            print(f"Error handling tool result: {e}")
            import traceback
            traceback.print_exc()

    def _extract_info_from_history(self):
        """Extract name, phone, email, company from conversation history"""
        info = {'name': None, 'phone': None, 'email': None, 'company': None}

        messages = self.chat_ctx.messages if hasattr(self.chat_ctx, 'messages') else []
        for msg in messages:
            if msg.role != "user":
                continue

            content = msg.content
            if isinstance(content, list):
                text="".join([str(c) for c in content])
            else:
                text = str(content)

            print("DEBUG: Processing user message: '{text}'")

            text_lower = text.lower()

            # Extract name - improved patterns
            if info['name']:
                name_patterns = [
                    r"(?: my name is|i'm|i am|this is|call me)\s+([a-zA-Z][a-zA-Z\s]+?)(?:\.|,|$|\sand\s|my phone)",
                    r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
                ]
                for pattern in name_patterns:
                    name_match = re.search(pattern, text, re.IGNORECASE)
                    if name_match:
                        name = name_match.group(1).strip()
                        # Cleanning up common false positives
                        if len(name) > 2 and not any(word in name.lower() for word in ['phone', 'email', 'company', 'work']):
                            info['name'] = name
                            break

            # Extract phone - improved patterns
            if info['phone']:
                phone_match = re.search(r"(?:phone|number|call|mobile|contact)?\s*(?:is|:)?\s*(\+?\d[\d\s\-\(\)]{7,})", text, re.IGNORECASE)
                if phone_match:
                    info['phone'] = phone_match.group(1).strip()
                elif re.search(r"\d{3}[\s\-]?\d{3}[\s\-]?\d{4}", text): #US Phone format, need to change it to Indian phone format
                    phone_match = re.search(r"(\d{3}[\s\-]?\d{3}[\s\-]?\d{4})", text)
                    if phone_match:
                        info['phone'] = phone_match.group(1).strip()

            # Extract email
            if info['email']:
                email_match = re.search(r"([a-zA-Z0-9._?+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text)
                if email_match:
                    info ['email'] = email_match.group(1).strip()

            # Extract company - improved patterns
            if info['company']:
                company_patterns = [
                    r"(?:work at|company is|from|work for|with|at)\s+([a-zA-Z][a-zA-Z\s&]+?)(?:\.|,|$|and\s)",
                    r"(?:company|employer)?\s*(?:is|:)\s*([a-zA-Z][a-zA-Z\s&]+?)(?:\.|,|$)",
                ]
                for pattern in company_patterns:
                    comapny_match = re.search(pattern, text, re.IGNORECASE)
                    if comapny_match:
                        company = comapny_match.group(1).strip()
                        # Cleaning up common false positives
                        if len(company) > 1 and not any(word in company.lower() for word in ['my', 'the', 'phone', 'email']):
                            info['company'] = company
                            break

        return info
    
    def _generate_response(self, user_input, collected_info, missing_fields):
        """"Generate appropriate response based on what we have and what we need"""

        # If the user only gave their name
        if collected_info.get('name') and not collected_info.get('phone'):
            return f"Thank you, {collected_info['name']}. What's your phone number?"
        
        # If we have name and phone but not email
        if collected_info.get('phone') and not collected_info.get('email'):
            return "Great! And what's your email address?"
        
        # If we have name, phone, email but not company
        if collected_info.get('email') and not collected_info.get('company'):
            return "Perfect. Which company do you work for?"
        
        # Default: ask for the first missing field
        if 'name' in missing_fields:
            return "Could you please tell me your full name?"
        elif 'phone number' in missing_fields:
            return "What is your phone number?"
        elif 'email' in missing_fields:
            return "And your email address?"
        elif 'company name' in missing_fields:
            return "Which company are working in?"
        
        return "Could you please repeat that?"
    
class MyCustomLLM(llm.LLM):
    def __init__(self):
        super().__init__()

    @property
    def label(self) -> str:
        return "MyCustomLLM"
    
    def chat(self, *, chat_ctx, fnc_ctx=None, **kwargs):
        tools = kwargs.get('tools', None)
        conn_options = kwargs.get('conn_options', None)
        return MyCustomLLMStream(
            self,
            chat_ctx=chat_ctx,
            #fnc_ctx=fnc_ctx,
            tools=tools,
            conn_options=conn_options
        )