from src.orchestrator.model import orchestrate
from src.orchestrator.router import run_workflow
import time

def execute(query: str):
    return run_workflow(orchestrate(query))

if __name__ == "__main__":
    print("Orchestrator container started. Idle mode enabled.")
    while True:
        time.sleep(3600)
