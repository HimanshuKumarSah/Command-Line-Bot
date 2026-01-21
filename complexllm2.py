import re
from livekit.agents import llm


NAME_REGEX = r"\b([a-zA-Z]{2,}(?:\s+[a-zA-Z]{2,})+)\b"
PHONE_REGEX = r"\b(\+?\d[\d\s\-]{7,}\d)\b"
EMAIL_REGEX = r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b"
COMPANY_REGEX = r"(?:company|organization|org)\s*(?:is|:)?\s*([a-zA-Z0-9 &.-]+)"


class MyCustomLLMStream(llm.LLMStream):
    def __init__(self, llm_instance, chat_ctx, fnc_ctx=None, tools=None, conn_options=None):
        self._llm_instance = llm_instance
        self._sent = False
        self._awaiting_user = False

        # ✅ PERSISTENT STATE (CRITICAL FIX)
        self.collected_info = {
            "name": None,
            "phone": None,
            "email": None,
            "company": None,
        }

        super().__init__(
            llm=llm_instance,
            chat_ctx=chat_ctx,
            fnc_ctx=fnc_ctx,
            tools=tools,
            conn_options=conn_options,
        )

    @property
    def label(self) -> str:
        return "MyCustomLLM"

    # -------------------------
    # INFO EXTRACTION
    # -------------------------
    def _extract_info_from_text(self, text: str):
        info = {
            "name": None,
            "phone": None,
            "email": None,
            "company": None,
        }

        if not text:
            return info

        name_match = re.search(NAME_REGEX, text)
        if name_match:
            info["name"] = name_match.group(1).strip().title()

        phone_match = re.search(PHONE_REGEX, text)
        if phone_match:
            info["phone"] = phone_match.group(1).strip()

        email_match = re.search(EMAIL_REGEX, text)
        if email_match:
            info["email"] = email_match.group(1).strip()

        company_match = re.search(COMPANY_REGEX, text, re.IGNORECASE)
        if company_match:
            info["company"] = company_match.group(1).strip()

        return info

    # -------------------------
    # MAIN LOOP
    # -------------------------
    async def _run(self):
        async for msg in super()._run():

            # 🔹 Initial assistant prompt (only once)
            if not self._sent:
                self._sent = True
                self._awaiting_user = True

                yield llm.ChatMessage(
                    role="assistant",
                    content="Hi! I’ll collect a few details. What is your full name?",
                )
                continue  # DO NOT return

            # 🔹 Ignore everything except a NEW user turn
            if msg.role != "user":
                continue

            # 🔹 Prevent double-processing while waiting
            if not self._awaiting_user:
                continue

            self._awaiting_user = False  # lock turn

            user_input = msg.content or ""

            extracted = self._extract_info_from_text(user_input)
            for k, v in extracted.items():
                if v:
                    self.collected_info[k] = v

            missing_fields = [k for k, v in self.collected_info.items() if not v]

            print("Collected info:", self.collected_info)
            print("Missing fields:", missing_fields)

            if missing_fields:
                field = missing_fields[0]

                yield llm.ChatMessage(
                    role="assistant",
                    content=f"Thanks. Could you please tell me your {field.replace('_', ' ')}?",
                )

                self._awaiting_user = True
                continue  # WAIT for next user input

            yield llm.ChatMessage(
                role="assistant",
                content=(
                    "Thank you! Here is what I have collected:\n"
                    f"Name: {self.collected_info['name']}\n"
                    f"Phone: {self.collected_info['phone']}\n"
                    f"Email: {self.collected_info['email']}\n"
                    f"Company: {self.collected_info['company']}"
                ),
            )

            self._awaiting_user = True
