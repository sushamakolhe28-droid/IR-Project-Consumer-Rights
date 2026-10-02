import math
from collections import Counter

class BM25Ranker:
    def __init__(self, index_obj, k1=1.5, b=0.75):
        self.index = index_obj.index
        self.doc_lengths = index_obj.doc_lengths
        self.num_docs = index_obj.num_docs
        self.k1 = k1
        self.b = b
        
        self.avgdl = sum(self.doc_lengths.values()) / max(1, self.num_docs)
        
    def score(self, query_tokens):
        scores = Counter()
        
        for term in query_tokens:
            if term in self.index:
                postings = self.index[term]
                df = len(postings)
                # IDF Formulation for BM25
                idf = math.log(((self.num_docs - df + 0.5) / (df + 0.5)) + 1)
                
                for doc_id, tf in postings:
                    length_norm = 1 - self.b + self.b * (self.doc_lengths[doc_id] / self.avgdl)
                    tf_component = (tf * (self.k1 + 1)) / (tf + self.k1 * length_norm)
                    scores[doc_id] += idf * tf_component
                    
        return scores.most_common()
