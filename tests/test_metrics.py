import unittest
from src.eval_metrics import precision_at_k, recall_at_k, average_precision, dcg_at_k, ndcg_at_k

class TestMetrics(unittest.TestCase):
    def test_precision_at_k(self):
        retrieved = ['d1', 'd2', 'd3', 'd4', 'd5']
        relevant = ['d2', 'd4', 'd6']
        # At 5: d2 and d4 are relevant. 2/5 = 0.4
        self.assertEqual(precision_at_k(retrieved, relevant, 5), 0.4)
        # At 3: d2 is relevant. 1/3 = 0.333...
        self.assertAlmostEqual(precision_at_k(retrieved, relevant, 3), 1/3)
        
    def test_recall_at_k(self):
        retrieved = ['d1', 'd2', 'd3', 'd4', 'd5']
        relevant = ['d2', 'd4', 'd6'] # 3 total relevant
        # At 5: d2, d4 retrieved. 2/3 = 0.666...
        self.assertAlmostEqual(recall_at_k(retrieved, relevant, 5), 2/3)
        
    def test_average_precision(self):
        retrieved = ['d1', 'd2', 'd3', 'd4', 'd5']
        relevant = ['d2', 'd4', 'd6']
        # Hits at 2 and 4.
        # P@2 = 1/2
        # P@4 = 2/4 = 1/2
        # Sum = 1.0. Total relevant = 3. AP = 1/3.
        self.assertAlmostEqual(average_precision(retrieved, relevant), 1/3)
        
    def test_ndcg_at_k(self):
        retrieved = ['d1', 'd2', 'd3']
        graded_relevant = {'d1': 3, 'd2': 2, 'd3': 1}
        # Ideal order is d1, d2, d3.
        # Since retrieved is in ideal order, nDCG should be 1.0
        self.assertEqual(ndcg_at_k(retrieved, graded_relevant, 3), 1.0)
        
        retrieved_bad = ['d3', 'd2', 'd1']
        self.assertTrue(ndcg_at_k(retrieved_bad, graded_relevant, 3) < 1.0)

if __name__ == '__main__':
    unittest.main()
