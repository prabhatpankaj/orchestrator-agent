from fastapi import FastAPI
from executor.execute import execute

app = FastAPI()

@app.post("/run")
def run_agent(payload: dict):
    query = payload.get("query", "")
    return execute(query)
