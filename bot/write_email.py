"""
write_email.py — Uses OpenAI to write a personalised follow-up email for each client.
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ─── Load your writing style samples ─────────────────────────────
def load_samples(filepath="email_samples.txt") -> str:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return ""  # no samples yet, AI will use a neutral style


SYSTEM_PROMPT = """
You are an assistant that writes professional but friendly follow-up reminder emails 
on behalf of the user. 

Rules:
- Keep it brief (3-5 sentences max)
- Sound human and natural, not robotic or overly formal
- Don't invent details not given to you
- Don't use filler phrases like "I hope this email finds you well"
- Sign off with the sender's name
- Match the tone and style of the sample emails provided

WRITING STYLE SAMPLES:
{samples}
"""


def create_outreach_email(client_data: dict) -> str:
    """
    Generate a personalised follow-up email for a single client.
    client_data should have: name, email, context (and optionally any other fields)
    """
    samples = load_samples()
    system = SYSTEM_PROMPT.format(samples=samples if samples else "No samples available.")

    user_prompt = f"""
Write a follow-up reminder email to {client_data['name']} ({client_data['email']}).
Context: {client_data.get('context', 'we were previously in touch')}
Sender name: {os.getenv('SENDER_NAME', 'Your Name')}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # Fast and free on Groq
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=300            # Emails should be short, no need for more
    )

    email_body = response.choices[0].message.content
    return email_body
