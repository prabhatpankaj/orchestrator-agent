import os
import ollama
import json

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
client = ollama.Client(host=OLLAMA_HOST)

def run(candidates):
    # Ensure input is a list
    if not isinstance(candidates, list):
         return {"error": "Input must be a list of job candidates.", "jobs": []}

    # Simplify context to save tokens
    simple_list = []
    for c in candidates:
        src = c.get("source", {})
        simple_list.append({
            "id": c.get("id"),
            "title": src.get("title"),
            "skills": src.get("skills"),
            "experience": src.get("experience"),
            # Truncate description
            "description": (src.get("description", "") or "")[:300]
        })

    prompt = f"""
You are an expert recruiter. Rank these candidates by relevance to the implied user intent.
Return valid JSON ONLY.
Format: {{"job_ids": ["best_id", "second_best_id", ...]}}

Candidates:
{json.dumps(simple_list, indent=2)}
"""
    
    try:
        response = client.chat(
            model="qwen2.5:3b-instruct",
            format="json",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response["message"]["content"]
        data = json.loads(content)
        ranked_ids = data.get("job_ids", [])
        
        # Reconstruct sorted list
        # Map ID -> full candidate object
        id_map = {c["id"]: c for c in candidates}
        
        sorted_jobs = []
        seen_ids = set()
        
        for jid in ranked_ids:
            if jid in id_map:
                sorted_jobs.append(id_map[jid])
                seen_ids.add(jid)
        
        # Add remaining jobs that weren't returned by LLM (fallback)
        for c in candidates:
            if c["id"] not in seen_ids:
                sorted_jobs.append(c)
                
        return {"jobs": sorted_jobs}

    except Exception as e:
        # Fallback: return original list in error case or partial failure
        print(f"Rerank failed: {e}")
        return {"jobs": candidates, "error": str(e)}
