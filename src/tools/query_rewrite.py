import os
import ollama

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
client = ollama.Client(host=OLLAMA_HOST)

PROMPT = """
Rewrite the user's job search query into a clean keyword format.
Extract only entities strictly present in the text:
- role
- skills
- experience
- location

Do NOT invent a location or experience if the user did not provide one.

Examples:
Input: "python dev in london" -> python developer london
Input: "java expert" -> java expert

Output MUST be a clean string. No quotes. No extra text.
"""

def run(text: str):
    response = client.chat(
        model="qwen2.5:3b-instruct",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": text}
        ]
    )
    return {"rewritten_query": response["message"]["content"].strip()}
