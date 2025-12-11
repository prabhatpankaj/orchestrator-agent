from src.tools.hybrid_core import hybrid_search

def run(query_obj):
    # Support both string and dictionary input
    if isinstance(query_obj, dict):
        query = query_obj.get("rewritten_query", "")
        loc = query_obj.get("location")
        exp = query_obj.get("experience")
    else:
        query = str(query_obj)
        loc = None
        exp = None

    candidates = hybrid_search(query, location=loc, experience=exp)

    # Rank by Experience (Ascending) then Hybrid Score (Descending)
    ranked = sorted(
        candidates, 
        key=lambda x: (
            x["source"].get("experience", float('inf')), 
            -(x["bm25"] + x["dense"])
        )
    )
    return ranked[:20]
