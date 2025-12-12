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
- experience: (integer, string, or null) Years of experience mentioned. Can be a single number (e.g. 5) or a range (e.g. "3-5").

Example:
Input: "backend role in bangalore for 5 years"
Output: {"keywords": "backend developer", "location": "bangalore", "experience": 5}

Input: "python remote"
Output: {"keywords": "python", "location": "remote", "experience": null}

Input: "frontend dev 3-5 years exp in pune"
Output: {"keywords": "frontend developer", "location": "pune", "experience": "3-5"}
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
        
        # Handle Experience Parsing
        exp = data.get("experience")
        final_exp = exp
        
        if isinstance(exp, str):
            # Try to parse "min-max" or "min to max"
            is_range = False
            parts = []
            
            if "-" in exp:
                parts = exp.split("-")
                is_range = True
            elif "to" in exp.lower():
                parts = exp.lower().split("to")
                is_range = True
                
            if is_range and len(parts) == 2:
                try:
                    min_e = int(parts[0].strip())
                    max_e = int(parts[1].strip())
                    final_exp = {"gte": min_e, "lte": max_e}
                except:
                    final_exp = None
            else:
                # If it's a string but NOT a range (e.g. "5+"), maybe try to parse single int?
                # For now, if fallback is needed, we could try extracting the first int.
                # But let's stick to what we know.
                pass
        
        return {
            "rewritten_query": data.get("keywords", text),
            "location": data.get("location"),
            "experience": final_exp
        }
    except:
        # Fallback
        return {"rewritten_query": text, "location": None, "experience": None}
