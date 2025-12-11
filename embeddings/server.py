from fastapi import FastAPI
from sentence_transformers import SentenceTransformer

app = FastAPI()

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

@app.post("/encode")
async def encode(payload: dict):
    text = payload["text"]
    embedding = model.encode(text).tolist()
    return {"embedding": embedding}
