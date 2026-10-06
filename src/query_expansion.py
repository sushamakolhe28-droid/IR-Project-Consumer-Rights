import os
import json
import re
from src.preprocess import preprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_EXPANSION_FILE = os.path.join(BASE_DIR, 'data', 'ontology', 'expansion.json')

class QueryExpander:
    def __init__(self, expansion_file=None):
        self.expansion_file = expansion_file or DEFAULT_EXPANSION_FILE
        self.mapping = self._load_mapping()
        # Sort multi-word keys first by length descending, then single-word keys
        self.multi_word_keys = sorted(
            [k for k in self.mapping if ' ' in k],
            key=lambda x: len(x),
            reverse=True
        )
        self.single_word_keys = [k for k in self.mapping if ' ' not in k]

    def _load_mapping(self):
        if not os.path.exists(self.expansion_file):
            return {}
        with open(self.expansion_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_expansion_terms(self, query_text, user_tokens=None):
        """
        Identify expansion terms for the query text.
        Returns a list of unique stemmed expansion tokens that are not in user_tokens.
        """
        if user_tokens is None:
            user_tokens = preprocess(query_text)
            
        user_tokens_set = set(user_tokens)
        matched_keys = set()
        text_lower = query_text.lower()

        # Check multi-word phrase matches
        for phrase in self.multi_word_keys:
            if phrase in text_lower:
                matched_keys.add(phrase)

        # Check single-word matches with word boundary
        for word in self.single_word_keys:
            if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
                matched_keys.add(word)

        expansion_tokens = []
        for key in matched_keys:
            targets = self.mapping.get(key, [])
            for target_word in targets:
                for stem in preprocess(target_word):
                    if stem not in user_tokens_set and stem not in expansion_tokens:
                        expansion_tokens.append(stem)

        return expansion_tokens

    def expand_query(self, query_text, user_tokens=None, return_added=False):
        """
        Expands the user query.
        Never removes the user's words.
        Appends expansion terms once (weights at 0.5 if ranker supports it, otherwise append once).
        """
        if user_tokens is None:
            user_tokens = preprocess(query_text)
            
        expansion_tokens = self.get_expansion_terms(query_text, user_tokens)
        expanded = list(user_tokens) + expansion_tokens
        
        if return_added:
            return expanded, expansion_tokens
        return expanded


# Module-level singleton and helper functions
_default_expander = None

def get_expander():
    global _default_expander
    if _default_expander is None:
        _default_expander = QueryExpander()
    return _default_expander

def expand_query(query_text, user_tokens=None, return_added=False):
    return get_expander().expand_query(query_text, user_tokens=user_tokens, return_added=return_added)

def get_expansion_terms(query_text, user_tokens=None):
    return get_expander().get_expansion_terms(query_text, user_tokens=user_tokens)
