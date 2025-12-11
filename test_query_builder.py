
import unittest
from src.tools.query_builder import ElasticsearchQueryBuilder

class TestQueryBuilder(unittest.TestCase):
    def test_text_search(self):
        qb = ElasticsearchQueryBuilder()
        qb.add_text_search("python", ["title"])
        query = qb.build_bm25_query()
        self.assertIn("query", query)
        self.assertIn("bool", query["query"])
        self.assertIn("must", query["query"]["bool"])
        self.assertEqual(query["query"]["bool"]["must"][0]["multi_match"]["query"], "python")

    def test_filters(self):
        qb = ElasticsearchQueryBuilder()
        qb.add_filter("location", "Hyderabad")
        query = qb.build_bm25_query()
        filters = query["query"]["bool"]["filter"]
        self.assertEqual(len(filters), 1)
        self.assertEqual(filters[0]["match"]["location"], "Hyderabad")

    def test_range_filter_dict(self):
        qb = ElasticsearchQueryBuilder()
        qb.add_range_filter("experience", {"gte": 3})
        query = qb.build_bm25_query()
        filters = query["query"]["bool"]["filter"]
        self.assertEqual(filters[0]["range"]["experience"]["gte"], 3)

    def test_boosting(self):
        qb = ElasticsearchQueryBuilder()
        qb.add_should_boost("skills", "kafka", 2.0)
        query = qb.build_bm25_query()
        should = query["query"]["bool"]["should"]
        self.assertEqual(should[0]["match"]["skills"]["query"], "kafka")
        self.assertEqual(should[0]["match"]["skills"]["boost"], 2.0)
        
    def test_knn(self):
        qb = ElasticsearchQueryBuilder()
        vector = [0.1, 0.2]
        qb.set_knn(vector)
        qb.add_filter("location", "US")
        query = qb.build_knn_query()
        self.assertIn("knn", query)
        self.assertEqual(query["knn"]["query_vector"], vector)
        self.assertIn("filter", query["knn"])

if __name__ == '__main__':
    unittest.main()
