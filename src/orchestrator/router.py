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
            if isinstance(rewritten, dict):
                inp = rewritten
        
        # 2. If rerank follows job_search, use the candidate list
        if tool_name == "rerank" and "job_search" in context:
            job_output = context["job_search"]
            # Correctly extract 'jobs' list from the previous tool's dict output
            if isinstance(job_output, dict) and "jobs" in job_output:
                inp = job_output["jobs"]
            elif isinstance(job_output, list):
                inp = job_output

        # --------------------------------------------------------
        # EXECUTION
        # --------------------------------------------------------
        if tool_name not in TOOL_MAP:
            output = {"error": f"Tool {tool_name} not found"}
        else:
            fn = TOOL_MAP[tool_name]
            try:
                output = fn(inp)
            except Exception as e:
                output = {"error": f"Error executing {tool_name}: {str(e)}"}

        # VALIDATION
        if not isinstance(output, dict):
             # Per instructions, enforce dict or raise/error
             output = {"error": f"Tool '{tool_name}' returned invalid format. Expected dict, got {type(output).__name__}."}

        # Store context
        context[tool_name] = output
        last_output = output

        results.append({
            "tool": tool_name,
            "input": inp, 
            "output": output
        })

    return results
