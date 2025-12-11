from src.tools.hybrid_core import hybrid_search

def run(query: str):
    candidates = hybrid_search(query)

    # Rank by hybrid score
    ranked = sorted(candidates, key=lambda x: x["bm25"] + x["dense"], reverse=True)
    return ranked[:20]
