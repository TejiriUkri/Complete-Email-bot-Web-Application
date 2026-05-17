"""
write_reply.py — Uses OpenAI to write a contextual reply based on the full email thread.
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def load_samples(filepath="email_samples.txt") -> str:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return ""


SYSTEM_PROMPT = """
You are an assistant that writes professional but friendly email replies on behalf of the user.

Rules:
- Read the full conversation thread carefully before replying
- Reply ONLY to what was said — don't add unrelated information
- Keep it brief and natural
- Never repeat what was already said in the thread
- Don't use filler phrases like "I hope this email finds you well"
- Match the tone and style of the writing samples provided
- Sign off with the sender's name

WRITING STYLE SAMPLES:
{samples}
"""


def create_reply(thread: dict) -> str:
    """
    Generate a reply based on the full conversation thread.
    
    thread should contain:
        - sender: email address of the person who replied
        - subject: email subject
        - history: list of dicts with 'role' (user/client) and 'content' (message text)
    """
    samples = load_samples()
    system = SYSTEM_PROMPT.format(samples=samples if samples else "No samples available.")

    # Format the conversation history into readable text for the AI
    # Only use the last 6 messages to stay within Groq's free tier token limit
    history = thread.get("history", [])
    recent_history = history[-6:] if len(history) > 6 else history

    conversation = ""
    for msg in recent_history:
        role_label = "Client" if msg["role"] == "client" else "Me"
        # Trim each individual message to 500 characters max
        content = msg['content'][:500] + "..." if len(msg['content']) > 500 else msg['content']
        conversation += f"\n{role_label}:\n{content}\n"

    user_prompt = f"""
Here is the full email conversation thread with {thread['sender']}:

{conversation}

Now write an appropriate reply continuing this conversation.
Sender name: {os.getenv('SENDER_NAME', 'Your Name')}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # Fast and free on Groq
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=400            # Replies can be slightly longer
    )

    reply_body = response.choices[0].message.content
    return reply_body
