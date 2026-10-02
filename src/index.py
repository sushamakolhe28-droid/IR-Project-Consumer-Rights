import os
import json
import math
import pickle
from collections import defaultdict, Counter

class InvertedIndex:
    def __init__(self):
        self.index = defaultdict(list) # term -> [(doc_id, tf), ...]
        self.doc_lengths = {}          # doc_id -> length
        self.collection_tf = Counter() # term -> total frequency in collection
        self.total_tokens = 0
        self.doc_metadata = {}         # doc_id -> metadata (like text, url)
        self.num_docs = 0
        
    def add_document(self, doc_id, tokens, metadata):
        self.num_docs += 1
        self.doc_lengths[doc_id] = len(tokens)
        self.total_tokens += len(tokens)
        self.doc_metadata[doc_id] = metadata
        
        term_freqs = Counter(tokens)
        for term, freq in term_freqs.items():
            self.index[term].append((doc_id, freq))
            self.collection_tf[term] += freq
            
    def save(self, filepath):
        with open(filepath, 'wb') as f:
            pickle.dump({
                'index': dict(self.index),
                'doc_lengths': self.doc_lengths,
                'collection_tf': dict(self.collection_tf),
                'total_tokens': self.total_tokens,
                'doc_metadata': self.doc_metadata,
                'num_docs': self.num_docs
            }, f)
            
    @classmethod
    def load(cls, filepath):
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        idx = cls()
        idx.index = defaultdict(list, data['index'])
        idx.doc_lengths = data['doc_lengths']
        idx.collection_tf = Counter(data['collection_tf'])
        idx.total_tokens = data['total_tokens']
        idx.doc_metadata = data['doc_metadata']
        idx.num_docs = data['num_docs']
        return idx

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    processed_dir = os.path.join(base_dir, 'data', 'processed')
    in_file = os.path.join(processed_dir, 'passages_preprocessed.jsonl')
    out_file = os.path.join(processed_dir, 'index.pkl')
    
    if not os.path.exists(in_file):
        print(f"Error: {in_file} not found. Run preprocess.py first.")
        return
        
    indexer = InvertedIndex()
    
    print("Building index...")
    with open(in_file, 'r', encoding='utf-8') as f:
        for line in f:
            passage = json.loads(line)
            doc_id = passage['passage_id']
            tokens = passage['tokens']
            # Store everything except the raw tokens list to save space
            metadata = {k: v for k, v in passage.items() if k != 'tokens'}
            indexer.add_document(doc_id, tokens, metadata)
            
    indexer.save(out_file)
    print(f"Index built and saved to {out_file}")
    print(f"Total documents: {indexer.num_docs}")
    print(f"Total unique terms: {len(indexer.index)}")

if __name__ == "__main__":
    main()
