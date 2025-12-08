import ollama
from orchestrator.prompts import SYSTEM_PROMPT

def orchestrate(user_query: str) -> str:
    response = ollama.chat(
        model="qwen2.5:3b-instruct",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query}
        ]
    )
    return response["message"]["content"]
