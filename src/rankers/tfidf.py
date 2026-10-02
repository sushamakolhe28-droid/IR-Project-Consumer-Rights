import math
from collections import Counter

class TFIDFRanker:
    def __init__(self, index_obj):
        self.index = index_obj.index
        self.doc_lengths = index_obj.doc_lengths
        self.num_docs = index_obj.num_docs
        
    def score(self, query_tokens):
        scores = Counter()
        
        for term in query_tokens:
            if term in self.index:
                postings = self.index[term]
                df = len(postings)
                idf = math.log10(self.num_docs / (df + 1))
                
                for doc_id, tf in postings:
                    # Normalized TF
                    tf_norm = tf / self.doc_lengths[doc_id]
                    scores[doc_id] += tf_norm * idf
                    
        # Return sorted by score
        return scores.most_common()
