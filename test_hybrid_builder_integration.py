
import sys
from unittest.mock import MagicMock

# Mock libraries before import
sys.modules["elasticsearch"] = MagicMock()
sys.modules["aerospike"] = MagicMock()
sys.modules["requests"] = MagicMock()

# Now we can safely import
from src.tools import hybrid_core

# Mock ES
mock_es = hybrid_core.ES
mock_es.search.return_value = {"hits": {"hits": []}}

# Input with dict experience
query = "backend"
loc = "Hyderabad"
exp = {"gte": 3, "lte": 5}

# Run
hybrid_core.hybrid_search(query, location=loc, experience=exp)

# Verify ES.search was called with correct filter via Builder
calls = mock_es.search.call_args_list

found_exp = False
print(f"Total ES.search calls: {len(calls)}")

for i, call in enumerate(calls):
    args, kwargs = call
    
    current_filters = []
    
    # Check BM25 call (has 'query')
    if 'query' in kwargs:
         try:
            current_filters = kwargs['query']['bool']['filter']
         except KeyError:
            pass
            
    # Check KNN (has 'knn')
    if 'knn' in kwargs:
         try:
            current_filters = kwargs['knn']['filter']
         except KeyError:
            pass

    for f in current_filters:
        if "range" in f and "experience" in f["range"]:
            if f["range"]["experience"] == exp:
                found_exp = True

if found_exp:
    print("SUCCESS: Dictionary experience correctly passed via Builder.")
else:
    print("FAILURE: Builder did not produce expected experience range filter.")
    sys.exit(1)
