import math
from collections import Counter

class LanguageModelRanker:
    def __init__(self, index_obj, smoothing='dirichlet', mu=2000, lambda_jm=0.5):
        self.index = index_obj.index
        self.doc_lengths = index_obj.doc_lengths
        self.collection_tf = index_obj.collection_tf
        self.total_tokens = index_obj.total_tokens
        self.num_docs = index_obj.num_docs
        
        self.smoothing = smoothing
        self.mu = mu
        self.lambda_jm = lambda_jm
        
    def _collection_prob(self, term):
        if self.total_tokens == 0:
            return 0
        return self.collection_tf.get(term, 0) / self.total_tokens
        
    def score(self, query_tokens):
        scores = Counter()
        
        # Pre-filter docs that contain at least one query term to speed up
        relevant_docs = set()
        for term in query_tokens:
            if term in self.index:
                for doc_id, _ in self.index[term]:
                    relevant_docs.add(doc_id)
                    
        for doc_id in relevant_docs:
            doc_len = self.doc_lengths[doc_id]
            log_prob = 0.0
            
            for term in query_tokens:
                # Get term frequency in document
                tf = 0
                if term in self.index:
                    for d_id, freq in self.index[term]:
                        if d_id == doc_id:
                            tf = freq
                            break
                            
                p_c = self._collection_prob(term)
                
                # If term is not in collection, skip to avoid log(0) - theoretically p_c should be > 0 with proper smoothing
                if p_c == 0:
                    continue
                    
                if self.smoothing == 'dirichlet':
                    # Dirichlet smoothing
                    # P(t|Md) = (tf + mu * P(t|Mc)) / (|d| + mu)
                    p_t_d = (tf + self.mu * p_c) / (doc_len + self.mu)
                    
                elif self.smoothing == 'jm':
                    # Jelinek-Mercer smoothing
                    # P(t|Md) = (1 - lambda) * (tf / |d|) + lambda * P(t|Mc)
                    p_t_d = (1 - self.lambda_jm) * (tf / doc_len if doc_len > 0 else 0) + self.lambda_jm * p_c
                    
                else:
                    raise ValueError("Smoothing must be 'dirichlet' or 'jm'")
                    
                log_prob += math.log(p_t_d)
                
            scores[doc_id] = log_prob
            
        return scores.most_common()
