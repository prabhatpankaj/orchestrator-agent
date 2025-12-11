from typing import Any, Dict, List, Optional, Union

class ElasticsearchQueryBuilder:
    def __init__(self):
        self.must_clauses = []
        self.filter_clauses = []
        self.should_clauses = []
        self.knn_config = {}
        self._source_excludes = []
        
    def add_text_search(self, text: str, fields: List[str], boost: float = 1.0):
        """Adds a multi_match query for full-text search."""
        if not text:
            return self
            
        clause = {
            "multi_match": {
                "query": text,
                "fields": fields
            }
        }
        if boost != 1.0:
            clause["multi_match"]["boost"] = boost
            
        self.must_clauses.append(clause)
        return self

    def add_filter(self, field: str, value: Any):
        """Adds a simple term/match filter."""
        if value is None:
            return self
        
        # Use 'match' for text fields (like location) to allow partial analysis if configured,
        # or 'term' for exact keyword. Keeping consistency with original 'match'.
        self.filter_clauses.append({"match": {field: value}})
        return self

    def add_range_filter(self, field: str, range_value: Union[Dict, int, float]):
        """
        Adds a range filter. 
        Supports passing a dictionary (e.g. {'gte': 1}) directly,
        or handles custom logic if needed by the caller before calling this.
        """
        if range_value is None:
            return self

        if isinstance(range_value, dict):
             self.filter_clauses.append({"range": {field: range_value}})
        else:
            # Fallback for simple values if called directly with a number? 
            # ideally the caller shapes the dict, but we can support equality or simple gte
            # sticking to dict based on previous requirements.
            pass
            
        return self

    def add_should_boost(self, field: str, value: Any, boost: float):
        """Adds a should clause to boost documents matching criteria."""
        if value is None:
            return self
            
        self.should_clauses.append({
            "match": {
                field: {
                    "query": value,
                    "boost": boost
                }
            }
        })
        return self
        
    def set_knn(self, vector: List[float], k: int = 50, num_candidates: int = 100):
        """Configures KNN search parameters."""
        self.knn_config = {
            "field": "embedding",
            "query_vector": vector,
            "k": k,
            "num_candidates": num_candidates
        }
        return self

    def set_source_excludes(self, excludes: List[str]):
        self._source_excludes = excludes
        return self

    def build_bm25_query(self) -> Dict[str, Any]:
        """Builds the body for a standard text search."""
        bool_query = {}
        
        if self.must_clauses:
            bool_query["must"] = self.must_clauses
            
        if self.filter_clauses:
            bool_query["filter"] = self.filter_clauses
            
        if self.should_clauses:
            bool_query["should"] = self.should_clauses
            # If we strictly want to filter, we don't assume min_match unless desired.
            
        body = {
            "query": {"bool": bool_query}
        }
        
        if self._source_excludes:
            body["_source"] = {"excludes": self._source_excludes}
            
        return body

    def build_knn_query(self) -> Dict[str, Any]:
        """Builds the body for a KNN search (with filters applied)."""
        if not self.knn_config:
            return {}
            
        knn_body = self.knn_config.copy()
        
        # Apply same filters to KNN
        if self.filter_clauses:
            knn_body["filter"] = self.filter_clauses
            
        body = {
            "knn": knn_body
        }
        
        if self._source_excludes:
            body["_source"] = {"excludes": self._source_excludes}
            
        return body
