from elasticsearch import Elasticsearch
import requests
import aerospike
import os
from src.tools.query_builder import ElasticsearchQueryBuilder

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

def hybrid_search(query: str, location: str = None, experience: int = None):
    vector = embed(query)
    
    # Initialize Builder
    builder = ElasticsearchQueryBuilder()
    builder.set_source_excludes(["embedding"])
    
    # 1. Text Search
    # Weighting: Title > Skills > Description
    builder.add_text_search(query, ["title^3", "skills^2", "description"])
    
    # 2. Filters
    builder.add_filter("location", location)
    
    if experience is not None:
        if isinstance(experience, dict):
             # Pass dictionary directly
             builder.add_range_filter("experience", experience)
        else:
             # Calculate range logic
             min_exp = max(0, experience)
             max_exp = experience + 5
             range_dict = {"gte": min_exp, "lte": max_exp}
             builder.add_range_filter("experience", range_dict)

    # 3. KNN Config
    builder.set_knn(vector, k=50, num_candidates=100)

    # Execute Searches
    try:
        bm25 = ES.search(
            index="jobs",
            size=50,
            **builder.build_bm25_query()
        )
    except Exception as e:
        print(f"BM25 Search Error: {e}")
        bm25 = {"hits": {"hits": []}}

    try:
        dense = ES.search(
            index="jobs",
            **builder.build_knn_query()
        )
    except Exception as e:
        print(f"Dense Search Error: {e}")
        dense = {"hits": {"hits": []}}

    # RRF (Reciprocal Rank Fusion)
    # score = 1 / (k + rank)
    k = 60
    scores = {}
    es_source_map = {}

    def add_score(hits, rank_type):
        for i, hit in enumerate(hits):
            jid = hit["_id"]
            if jid not in scores:
                scores[jid] = 0
                es_source_map[jid] = hit["_source"]
            
            # 1 / (k + rank), rank is 1-based usually, or 0-based. 
            # using i+1 for 1-based rank
            scores[jid] += 1 / (k + i + 1)

    add_score(bm25["hits"]["hits"], "bm25")
    add_score(dense["hits"]["hits"], "dense")

    # Fetch Details from Aerospike (Preferred Source)
    all_ids = list(scores.keys())
    details_map = get_aerospike_details(all_ids)

    final_results = []
    for jid, score in scores.items():
        # Source Priority: Aerospike > Elasticsearch
        source = details_map.get(jid) or es_source_map.get(jid)
        
        if source:
            final_results.append({
                "id": jid,
                "source": source,
                "score": score,
                # Keep raw scores for debug if needed, but RRF is the main one now
                "bm25_score": 0, # Not tracking individual raw scores anymore for simplicity
                "dense_score": 0
            })
    
    # Sort by RRF score descending
    final_results.sort(key=lambda x: x["score"], reverse=True)
    
    return final_results
