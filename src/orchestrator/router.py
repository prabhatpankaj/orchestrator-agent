import json
from src.tools.query_rewrite import run as query_rewrite
from src.tools.job_search import run as job_search
from src.tools.rerank import run as rerank

TOOL_MAP = {
    "query_rewrite": query_rewrite,
    "job_search": job_search,
    "rerank": rerank,
}

def run_workflow(json_text: str):
    workflow = json.loads(json_text)

    results = []
    for step in workflow.get("steps", []):
        tool_name = step["tool"]
        inp = step["input"]
        fn = TOOL_MAP[tool_name]

        output = fn(inp)

        results.append({
            "tool": tool_name,
            "input": inp,
            "output": output
        })

    return results
