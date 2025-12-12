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

    candidate_list = []
    
    # Clean inputs
    if query:
        query = query.strip()
        
    # If query is empty but location/experience provided, we still run search (filtering).
    # If EVERYTHING is empty, return empty list.
    if not query and not loc and exp is None:
         return {"jobs": []}

    candidate_list = hybrid_search(query, location=loc, experience=exp)

    # Rank by Experience (Ascending) then by RRF Score (Descending)
    # We use valid experience values first. Missing experience maps to infinity (end of list).
    ranked = sorted(
        candidate_list, 
        key=lambda x: (
            x["source"].get("experience", float('inf')), 
            -x["score"]
        )
    )
    return {"jobs": ranked[:20]}
