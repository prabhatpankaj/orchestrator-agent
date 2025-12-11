from elasticsearch import Elasticsearch
import requests
import aerospike
import os

# 1. Connect to ES
ES = Elasticsearch("http://elasticsearch:9200")

# 2. Connect to Aerospike
AS_HOST = os.getenv("AEROSPIKE_HOST", "aerospike")
AS_PORT = int(os.getenv("AEROSPIKE_PORT", 3000))
AS_CONFIG = {"hosts": [(AS_HOST, AS_PORT)]}
# We initialize client lazily or globally. 
# For a script/tool-per-request model, we might connect here. 
# But python client connection is heavy? Assuming tool runs in long-lived container (orchestrator).
try:
    AS_CLIENT = aerospike.client(AS_CONFIG).connect()
except Exception as e:
    print(f"Failed to connect to Aerospike: {e}")
    AS_CLIENT = None

EMBED_API = "http://embeddings:8002/encode"
AS_NAMESPACE = "test"
AS_SET = "jobs"

def embed(text: str):
    response = requests.post(EMBED_API, json={"text": text})
    return response.json()["embedding"]

def get_aerospike_details(job_ids):
    if not AS_CLIENT or not job_ids:
        return {}
    
    keys = [(AS_NAMESPACE, AS_SET, str(jid)) for jid in job_ids]
    
    # get_many returns: ((key_tuple), meta, bins)
    try:
        records = AS_CLIENT.get_many(keys)
        results = {}
        for rec in records:
            # rec is ((ns, set, digest, pk), meta, bins)
            # If record not found, bins is None
            key_tuple, meta, bins = rec
            if bins:
                # key_tuple[3] might be the PK if stored, or we rely on order.
                # get_many usually preserves order or we can map by PK if we have it?
                # Actually key_tuple[3] is the user_key if policy.send_key is true.
                # Let's map by job_id inside bins if available, or just trust the input list?
                # Safer: bins['job_id']
                if "job_id" in bins:
                    results[bins["job_id"]] = bins
        return results
    except Exception as e:
        print(f"Aerospike batch fetch error: {e}")
        return {}

def hybrid_search(query: str):
    vector = embed(query)

    # Sparse (BM25) - ID only
    bm25 = ES.search(
        index="jobs",
        size=100,
        _source=False, # Fetch ID only
        query={"multi_match": {"query": query, "fields": ["title", "description", "skills"]}},
    )

    # Dense (KNN) - ID only
    dense = ES.search(
        index="jobs",
        _source=False, # Fetch ID only
        knn={"field": "embedding", "query_vector": vector, "k": 100, "num_candidates": 200},
    )

    # Collect Scores
    scores = {}

    for hit in bm25["hits"]["hits"]:
        jid = hit["_id"]
        scores[jid] = {"bm25": hit["_score"], "dense": 0}

    for hit in dense["hits"]["hits"]:
        jid = hit["_id"]
        if jid not in scores:
            scores[jid] = {"bm25": 0, "dense": hit["_score"]}
        else:
            scores[jid]["dense"] = hit["_score"]

    # Fetch Details from Aerospike
    all_ids = list(scores.keys())
    details_map = get_aerospike_details(all_ids)

    final_results = []
    for jid, score_data in scores.items():
        if jid in details_map:
            final_results.append({
                "source": details_map[jid], # Use Aerospike data as source
                "bm25": score_data["bm25"],
                "dense": score_data["dense"]
            })
    
    return final_results
