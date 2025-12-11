import os
import ollama
import json

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
client = ollama.Client(host=OLLAMA_HOST)

def run(candidates):
    prompt = f"""
Rank these jobs best to worst.
Return JSON: {{"job_ids": ["id1", "id2", ...]}}
Jobs: {candidates}
"""
    
    response = client.chat(
        model="qwen2.5:3b-instruct",
        format="json",
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(response["message"]["content"])
