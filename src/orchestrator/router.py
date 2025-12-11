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
    context = {}
    last_output = None

    for step in workflow.get("steps", []):
        tool_name = step["tool"]
        inp = step["input"]
        
        # --------------------------------------------------------
        # INTELLIGENT CONTEXT PASSING (Piping)
        # --------------------------------------------------------
        # 1. If job_search follows query_rewrite, use the rewritten query
        if tool_name == "job_search" and "query_rewrite" in context:
            rewritten = context["query_rewrite"]
            # It returns a dict {"rewritten_query": "..."}
            if isinstance(rewritten, dict) and "rewritten_query" in rewritten:
                inp = rewritten["rewritten_query"]
        
        # 2. If rerank follows job_search, use the candidate list
        if tool_name == "rerank" and "job_search" in context:
            candidates = context["job_search"]
            if isinstance(candidates, list):
                inp = candidates

        # --------------------------------------------------------
        # EXECUTION
        # --------------------------------------------------------
        fn = TOOL_MAP[tool_name]
        try:
            output = fn(inp)
        except Exception as e:
            output = f"Error executing {tool_name}: {str(e)}"

        # Store context
        context[tool_name] = output
        last_output = output

        results.append({
            "tool": tool_name,
            "input": inp, 
            "output": output
        })

    return results
