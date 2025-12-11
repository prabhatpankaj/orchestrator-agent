import asyncio
import aiomysql
import aerospike
from elasticsearch import Elasticsearch
import os
import time
import requests
import json
import argparse
from datetime import datetime, timedelta

# Config
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DB = os.getenv("MYSQL_DB", "jobs_db")

AS_HOST = os.getenv("AEROSPIKE_HOST", "localhost")
AS_PORT = int(os.getenv("AEROSPIKE_PORT", 3000))
AS_NAMESPACE = "test"
AS_SET = "jobs"

ES_HOST = os.getenv("ES_HOST", "http://elasticsearch:9200")
EMBED_API = os.getenv("EMBEDDING_API", "http://embeddings:8002/encode")
INDEX_NAME = "jobs"

# Global Clients
es = Elasticsearch(ES_HOST)

def get_aerospike_client():
    config = {"hosts": [(AS_HOST, AS_PORT)]}
    client = aerospike.client(config).connect()
    return client

async def get_mysql_pool():
    return await aiomysql.create_pool(
        host=MYSQL_HOST, port=3306,
        user=MYSQL_USER, password=MYSQL_PASSWORD,
        db=MYSQL_DB, loop=asyncio.get_running_loop()
    )

def embed_text_sync(text):
    try:
        resp = requests.post(EMBED_API, json={"text": text}, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("embedding", [])
    except Exception as e:
        print(f"Embedding error: {e}")
    return [0.0] * 384

async def process_job(row, as_client):
    job_id, title, desc, loc, exp, skills = row
    
    # Text for embedding
    full_text = f"{title} {desc} {skills} {loc}"
    
    # 1. Embed (CPU bound/Blocking IO -> Thread)
    vector = await asyncio.to_thread(embed_text_sync, full_text)
    
    # 2. Update Aerospike (Full Data)
    key = (AS_NAMESPACE, AS_SET, str(job_id))
    bins = {
        "job_id": str(job_id),
        "title": title,
        "description": desc,
        "location": loc,
        "experience": exp,
        "skills": skills
    }
    # Write to AS (sync client, run in thread or if fast enough just run)
    # Aerospike python client is sync.
    try:
        as_client.put(key, bins)
    except Exception as e:
        print(f"AS Error {job_id}: {e}")

    # 3. Update Elasticsearch (Index Fields + Vector)
    doc = {
        "job_id": str(job_id),
        "title": title,
        "description": desc,
        "skills": skills,
        "location": loc,
        "experience": exp,
        "embedding": vector
    }
    
    # ES Index
    try:
        es.index(index=INDEX_NAME, id=str(job_id), document=doc)
    except Exception as e:
        print(f"ES Error {job_id}: {e}")

    return job_id

async def run_indexer(mode="full"):
    print(f"Starting Indexer (Mode: {mode})...")
    
    pool = await get_mysql_pool()
    as_client = get_aerospike_client()
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                if mode == "full":
                    print("Fetching ALL jobs from MySQL...")
                    await cur.execute("SELECT job_id, title, description, location, experience, skills FROM jobs")
                else:
                    # Partial: Fetch jobs updated in last 1 hour
                    print("Fetching RECENT jobs from MySQL...")
                    await cur.execute("SELECT job_id, title, description, location, experience, skills FROM jobs WHERE updated_at >= NOW() - INTERVAL 1 HOUR")
                
                rows = await cur.fetchall()
                print(f"Found {len(rows)} jobs to process.")
                
                tasks = []
                for row in rows:
                    tasks.append(process_job(row, as_client))
                    
                    if len(tasks) >= 50:
                        await asyncio.gather(*tasks)
                        tasks = []
                        print(".", end="", flush=True)
                
                if tasks:
                    await asyncio.gather(*tasks)
                    
        print(f"\n✅ Indexing complete.")
        
    finally:
        as_client.close()
        pool.close()
        await pool.wait_closed()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full", "partial"], default="full")
    args = parser.parse_args()
    
    # Ensure ES index exists
    if not es.indices.exists(index=INDEX_NAME):
        print("Creating ES index...")
        # (Simplified creation, assuming strict schema mapping is in index_jobs.py, 
        # but here we rely on dynamic mapping or pre-existing index. 
        # Ideally we call the create_index logic from index_jobs.py)
        pass 

    asyncio.run(run_indexer(args.mode))
