import os
import ollama

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
client = ollama.Client(host=OLLAMA_HOST)

PROMPT = """
Rewrite the user's job search query into a clean keyword format.
Extract:
- role
- skills (if present)
- experience
- location
Output MUST be a clean string, e.g.:

python developer 6 years bangalore

No quotes. No extra text.
"""

def run(text: str):
    response = client.chat(
        model="qwen2.5:3b-instruct",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": text}
        ]
    )
    return response["message"]["content"].strip()
