import json
from tools import (
    job_search,
    salary_predict,
    resume_parser,
    jd_parser,
    web_search,
    sql_agent,
    code_interpreter
)

TOOL_MAP = {
    "job_search": job_search.run,
    "salary_predict": salary_predict.run,
    "resume_parser": resume_parser.run,
    "jd_parser": jd_parser.run,
    "web_search": web_search.run,
    "sql_agent": sql_agent.run,
    "code_interpreter": code_interpreter.run,
}

def run_workflow(orchestrator_output: str):
    try:
        workflow = json.loads(orchestrator_output)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON output from orchestrator.")

    results = []

    for step in workflow.get("steps", []):
        tool = step["tool"]
        input_data = step["input"]

        if tool not in TOOL_MAP:
            raise ValueError(f"Unknown tool '{tool}'")

        output = TOOL_MAP[tool](input_data)

        results.append({
            "tool": tool,
            "input": input_data,
            "output": output
        })

    return results
