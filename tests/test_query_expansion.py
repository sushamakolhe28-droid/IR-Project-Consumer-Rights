import os
import re
import json
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASSAGES_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'passages.jsonl')
EXPANSION_FILE = os.path.join(BASE_DIR, 'data', 'ontology', 'expansion.json')

from src.query_expansion import expand_query, get_expansion_terms, QueryExpander
from src.preprocess import preprocess

class TestQueryExpansion(unittest.TestCase):

    def test_all_target_words_occur_in_corpus(self):
        """Verify that every target word in expansion.json occurs in data/processed/passages.jsonl."""
        self.assertTrue(os.path.exists(EXPANSION_FILE), f"{EXPANSION_FILE} not found")
        self.assertTrue(os.path.exists(PASSAGES_FILE), f"{PASSAGES_FILE} not found")
        
        with open(EXPANSION_FILE, 'r', encoding='utf-8') as f:
            expansion_map = json.load(f)
            
        corpus_words = set()
        with open(PASSAGES_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                passage = json.loads(line)
                for w in re.findall(r'[a-z0-9]+', passage['text'].lower()):
                    corpus_words.add(w)
                    
        all_targets = set()
        for term, targets in expansion_map.items():
            self.assertIsInstance(targets, list, f"Targets for {term} must be a list")
            for target_word in targets:
                all_targets.add(target_word.lower().strip())
                
        missing_words = [w for w in all_targets if w not in corpus_words]
        self.assertEqual(
            missing_words, [],
            f"Target words not found in passages.jsonl: {missing_words}"
        )

    def test_expansion_never_removes_user_words(self):
        """Verify that expand_query only appends terms and never removes original user tokens."""
        query = "I bought a washing machine and it is broken"
        user_tokens = preprocess(query)
        expanded_tokens = expand_query(query, user_tokens=user_tokens)
        
        # User tokens must appear intact as the prefix of expanded_tokens
        self.assertEqual(expanded_tokens[:len(user_tokens)], user_tokens)
        # Expansion tokens should have been added
        self.assertGreater(len(expanded_tokens), len(user_tokens))

    def test_expansion_appends_once_no_duplicates(self):
        """Verify that expansion terms are appended once and no duplicate expansion tokens are added."""
        query = "I want a refund and money back"
        expanded, added = expand_query(query, return_added=True)
        # Added terms must all be unique
        self.assertEqual(len(added), len(set(added)))

    def test_counterfeit_fake_expansion(self):
        """Verify counterfeit/fake triggers false, misleading, description."""
        query = "bought shoes but counterfeit"
        added = get_expansion_terms(query)
        # Stemmed versions of false, misleading, description
        self.assertTrue(any(t in added for t in ['fals', 'mislead', 'descript']))

if __name__ == '__main__':
    unittest.main()
