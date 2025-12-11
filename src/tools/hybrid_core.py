from elasticsearch import Elasticsearch
import requests
from sentence_transformers import SentenceTransformer

ES = Elasticsearch("http://elasticsearch:9200")

EMBED_API = "http://embeddings:8002/encode"

def embed(text: str):
    response = requests.post(EMBED_API, json={"text": text})
    return response.json()["embedding"]

def hybrid_search(query: str):
    vector = embed(query)

    # Sparse (BM25)
    bm25 = ES.search(
        index="jobs",
        size=100,
        query={"multi_match": {"query": query, "fields": ["title", "description", "skills"]}},
    )

    # Dense (KNN)
    dense = ES.search(
        index="jobs",
        knn={"field": "embedding", "query_vector": vector, "k": 100, "num_candidates": 200},
    )

    # Merge results
    results = {}

    for hit in bm25["hits"]["hits"]:
        results[hit["_id"]] = {
            "source": hit["_source"],
            "bm25": hit["_score"],
            "dense": 0
        }

    for hit in dense["hits"]["hits"]:
        if hit["_id"] not in results:
            results[hit["_id"]] = {
                "source": hit["_source"],
                "bm25": 0,
                "dense": hit["_score"]
            }
        else:
            results[hit["_id"]]["dense"] = hit["_score"]

    return list(results.values())
