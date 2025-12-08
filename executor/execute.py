from orchestrator.model import orchestrate
from orchestrator.router import run_workflow

def execute(user_query: str):
    plan = orchestrate(user_query)
    return run_workflow(plan)
