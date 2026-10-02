import unittest
from collections import Counter
from src.preprocess import preprocess, normalize_hinglish
from src.ie import extract_amount, extract_platform
from src.rankers.tfidf import TFIDFRanker
from src.rankers.bm25 import BM25Ranker

# Mock Index Object for testing rankers
class MockIndex:
    def __init__(self):
        # Three small documents
        # d1: "fraud fake"
        # d2: "refund amount"
        # d3: "fraud refund fake"
        self.index = {
            'fraud': [('d1', 1), ('d3', 1)],
            'fake': [('d1', 1), ('d3', 1)],
            'refund': [('d2', 1), ('d3', 1)],
            'amount': [('d2', 1)]
        }
        self.doc_lengths = {'d1': 2, 'd2': 2, 'd3': 3}
        self.num_docs = 3
        self.total_tokens = 7
        self.collection_tf = Counter({'fraud': 2, 'fake': 2, 'refund': 2, 'amount': 1})

class TestComponents(unittest.TestCase):

    def test_tokenizer_and_hinglish(self):
        # Test Hinglish translation
        text = "I want my paisa wapas because of this dhokha"
        normalized = normalize_hinglish(text)
        self.assertIn("refund", normalized)
        self.assertIn("fraud", normalized)
        
        # Test preprocessing (lowercasing, punctuation, stop words)
        tokens = preprocess(text)
        self.assertIn("refund", tokens)
        self.assertIn("fraud", tokens)
        self.assertNotIn("paisa", tokens)

    def test_extractor(self):
        # Test Amount Extractor
        text = "I lost Rs. 5,000 on amazon"
        amount = extract_amount(text)
        self.assertEqual(amount, 5000)
        
        # Test Platform Extractor
        platforms = extract_platform(text)
        self.assertIn("Amazon", platforms)

    def test_tfidf_ranker(self):
        index = MockIndex()
        ranker = TFIDFRanker(index)
        
        query = ["fraud"]
        results = ranker.score(query)
        # Both d1 and d3 have 'fraud'. 
        # d1 length is 2, tf_norm = 1/2.
        # d3 length is 3, tf_norm = 1/3.
        # So d1 should score higher than d3.
        
        self.assertTrue(len(results) == 2)
        self.assertEqual(results[0][0], 'd1')
        self.assertEqual(results[1][0], 'd3')

    def test_bm25_ranker(self):
        index = MockIndex()
        ranker = BM25Ranker(index)
        
        query = ["refund"]
        results = ranker.score(query)
        
        # Both d2 and d3 have 'refund'.
        # d2 length is 2 (shorter than average if we check), d3 is 3.
        # Shorter document should rank higher in BM25 for the same term frequency.
        self.assertTrue(len(results) == 2)
        self.assertEqual(results[0][0], 'd2')
        self.assertEqual(results[1][0], 'd3')

if __name__ == '__main__':
    unittest.main()
