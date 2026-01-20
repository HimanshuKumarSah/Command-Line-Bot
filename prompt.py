SYSTEM_PROMPT = """
You are a Verification Bot. You must collect: Name, Phone, Email, Company.
1. Ask for missing details.
2. Once you have all 4, call 'verify_and_save'.
3. If the tool says MATCH, say goodbye and call 'end_call'.
4. If the tool says UPDATED, read updated info, say goodbye and call 'end_call'.
"""

def get_missing_info_query(collected_data):
    # Custom logic to decide what to ask next
    if not collected_data.get('name'): return "What is your full name?"
    if not collected_data.get('phone'): return "What is your phone number?"
    if not collected_data.get('email'): return "What is your email address?"
    if not collected_data.get('company'): return "Which company do you work for?"
    return None