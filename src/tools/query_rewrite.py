import os
import ollama

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
client = ollama.Client(host=OLLAMA_HOST)

import json

PROMPT = """
Analyze the user's job search query and extract structured parameters.
Return valid JSON ONLY.

Fields:
- keywords: (string) Core search terms (roles, skills, tech stack). Remove location/experience words.
- location: (string or null) The city or region specified.
- experience: (integer or null) Years of experience mentioned.

Example:
Input: "backend role in bangalore for 5 years"
Output: {"keywords": "backend developer", "location": "bangalore", "experience": 5}

Input: "python remote"
Output: {"keywords": "python", "location": "remote", "experience": null}
"""

def run(text: str):
    response = client.chat(
        model="qwen2.5:3b-instruct",
        format="json",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": text}
        ]
    )
    try:
        data = json.loads(response["message"]["content"])
        # Ensure keys exist
        return {
            "rewritten_query": data.get("keywords", text),
            "location": data.get("location"),
            "experience": data.get("experience")
        }
    except:
        # Fallback
        return {"rewritten_query": text, "location": None, "experience": None}
