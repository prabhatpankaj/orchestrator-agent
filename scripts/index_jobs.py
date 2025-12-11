import pandas as pd
import requests
from elasticsearch import Elasticsearch
import time
import json
import os
from math import ceil
import math

# -----------------------------------------
# CONFIG
# -----------------------------------------
ES_HOST = os.getenv("ES_HOST", "http://elasticsearch:9200")
EMBED_URL = os.getenv("EMBEDDING_API", "http://embeddings:8002/encode")
INDEX_NAME = "jobs"
VECTOR_DIMS = 384
BATCH_SIZE = 200  # safer for ES bulk ingestion

es = Elasticsearch(ES_HOST)


# -----------------------------------------
# WAIT FOR ES TO BE READY
# -----------------------------------------
def wait_for_es():
    print("Waiting for Elasticsearch...")
    while True:
        try:
            if es.ping():
                print("Elasticsearch is ready.")
                return
        except Exception:
            pass
        time.sleep(3)


# -----------------------------------------
# CREATE INDEX (BM25 + VECTOR)
# -----------------------------------------
def create_index():
    if es.indices.exists(index=INDEX_NAME):
        print(f"Index '{INDEX_NAME}' already exists. Deleting...")
        es.indices.delete(index=INDEX_NAME)

    mapping = {
        "mappings": {
            "properties": {
                "job_id": {"type": "keyword"},
                "title": {"type": "text", "similarity": "BM25"},
                "description": {"type": "text", "similarity": "BM25"},
                "location": {"type": "keyword"},
                "experience": {"type": "integer"},
                "skills": {"type": "text", "similarity": "BM25"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": VECTOR_DIMS,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }

    es.indices.create(index=INDEX_NAME, body=mapping)
    print(f"Created index '{INDEX_NAME}' with BM25 + dense vector.")


# -----------------------------------------
# SANITIZE EMBEDDING (fix NaN, inf, None)
# -----------------------------------------
def sanitize_embedding(vec):
    clean = []
    for v in vec:
        if v is None or isinstance(v, str):
            clean.append(0.0)
        else:
            try:
                if math.isnan(v) or math.isinf(v):
                    clean.append(0.0)
                else:
                    clean.append(float(v))
            except Exception:
                clean.append(0.0)
    return clean


# -----------------------------------------
# SANITIZE DOCUMENT FIELDS (fix CSV NaN → "")
# -----------------------------------------
def sanitize_document(d):
    clean = {}
    for k, v in d.items():
        if v is None:
            clean[k] = ""
        elif isinstance(v, float) and math.isnan(v):
            clean[k] = ""
        else:
            clean[k] = v
    return clean


# -----------------------------------------
# EMBEDDING WITH RETRIES + VALIDATION
# -----------------------------------------
def embed_text(text: str):
    payload = {"text": text}

    for attempt in range(5):
        try:
            resp = requests.post(EMBED_URL, json=payload, timeout=20)

            if resp.status_code == 200:
                emb = resp.json().get("embedding", [])

                # Fix embed size mismatch
                if len(emb) != VECTOR_DIMS:
                    print(f"⚠️ Warning: bad embedding dims {len(emb)}. Padding/truncating.")
                    emb = (emb + [0.0] * VECTOR_DIMS)[:VECTOR_DIMS]

                # Fix NaN / inf etc
                emb = sanitize_embedding(emb)

                return emb

            print(f"❌ Embedding error status {resp.status_code}, retrying...")

        except Exception as e:
            print(f"❌ Embedding exception: {e}. Retrying...")

        time.sleep(2)

    print("❌ Failed to embed text after 5 retries. Using zero vector.")
    return [0.0] * VECTOR_DIMS


# -----------------------------------------
# BULK INDEXING WITH DEBUG LOGS
# -----------------------------------------
def bulk_index(df):
    total_batches = ceil(len(df) / BATCH_SIZE)
    print(f"Starting bulk indexing in {total_batches} batches...")

    for batch_idx in range(total_batches):
        batch = df.iloc[batch_idx * BATCH_SIZE : (batch_idx + 1) * BATCH_SIZE]

        ops = []
        for _, row in batch.iterrows():
            emb = embed_text(row["description"])

            action = {
                "index": {
                    "_index": INDEX_NAME,
                    "_id": str(row["job_id"])
                }
            }

            # FIX: sanitize CSV NaN values
            doc = sanitize_document(row.to_dict())

            # Add embedding
            doc["embedding"] = emb

            ops.append(json.dumps(action))
            ops.append(json.dumps(doc))

        payload = "\n".join(ops) + "\n"
        resp = es.bulk(body=payload)

        print(f"Batch {batch_idx+1}/{total_batches} indexed. Errors: {resp.get('errors')}")

        # If there are errors — print first and stop
        if resp.get("errors"):
            print("\n❌ ERROR DETAILS:")
            for item in resp["items"]:
                if "error" in item["index"]:
                    print(json.dumps(item["index"]["error"], indent=2))
                    break
            print("‼️ Fix required — stopping indexing.")
            return

    print("🎉 All batches indexed successfully! No bulk errors.")


# -----------------------------------------
# MAIN
# -----------------------------------------
def main():
    wait_for_es()
    create_index()

    print("Loading CSV file...")
    df = pd.read_csv("jobs.csv")
    print(f"Loaded {len(df)} job records.")

    bulk_index(df)

    print("✅ Job ingestion complete.")


if __name__ == "__main__":
    main()
