import os
import ollama
from src.orchestrator.prompts import SYSTEM_PROMPT

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
client = ollama.Client(host=OLLAMA_HOST)

def orchestrate(user_query: str) -> str:
    response = client.chat(
        model="qwen2.5:3b-instruct",
        format="json",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ],
    )
    return response["message"]["content"]
