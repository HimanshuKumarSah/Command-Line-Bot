import uuid
from livekit.agents import llm

class MyCustomLLMStream(llm.LLMStream):
    def __init__(self, llm_instance, chat_ctx, fnc_ctx=None, tools=None, conn_options=None):
        # Pass all required parameters to parent
        super().__init__(
            llm=llm_instance, 
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options or llm.LLMConnOptions()
        )
        self._fnc_ctx = fnc_ctx
        self._sent = False
    
    async def _run(self):
        """Required abstract method - this is where the LLM processing happens"""
        if self._sent:
            return
        
        self._sent = True
        
        try:
            last_msg = self.chat_ctx.messages[-1]
            content = last_msg.content
            if isinstance(content, list):
                msg_text = "".join([str(c) for c in content]).lower()
            else:
                msg_text = str(content).lower()
        except:
            msg_text = ""
        
        # Check for goodbye
        if "bye" in msg_text or "goodbye" in msg_text:
            chunk = llm.ChatChunk(
                id=str(uuid.uuid4()),
                delta=llm.ChoiceDelta(
                    role="assistant",
                    tool_calls=[llm.FunctionToolCall(id="c1", name="end_call", arguments="{}")]
                )
            )
        else:
            chunk = llm.ChatChunk(
                id=str(uuid.uuid4()),
                delta=llm.ChoiceDelta(role="assistant", content="I see. Please continue.")
            )
        
        # Push the chunk to the queue
        self._event_ch.send_nowait(chunk)

class MyCustomLLM(llm.LLM):
    def __init__(self):
        super().__init__()
    
    @property
    def label(self) -> str:
        """Return a label for this LLM"""
        return "MyCustomLLM"
    
    def chat(self, *, chat_ctx, fnc_ctx=None, **kwargs):
        # Extract tools and conn_options from kwargs if they exist
        tools = kwargs.get('tools', None)
        conn_options = kwargs.get('conn_options', None)
        return MyCustomLLMStream(
            self, 
            chat_ctx=chat_ctx, 
            fnc_ctx=fnc_ctx,
            tools=tools,
            conn_options=conn_options
        )