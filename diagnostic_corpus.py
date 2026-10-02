import os
import json
import numpy as np

base_dir = os.path.dirname(__file__)
data_dir = os.path.join(base_dir, 'data')
raw_dir = os.path.join(data_dir, 'raw')
processed_dir = os.path.join(data_dir, 'processed')
passages_file = os.path.join(processed_dir, 'passages.jsonl')
manifest_file = os.path.join(processed_dir, 'corpus_manifest.json')
failures_file = os.path.join(processed_dir, 'validation_failures.json')

def main():
    print('--- CORPUS HEALTH DIAGNOSTICS ---')
    
    docs = set()
    doc_stats = {}
    passages_count = 0
    lengths = []
    vocab = set()
    
    if os.path.exists(passages_file):
        with open(passages_file, 'r', encoding='utf-8') as f:
            for line in f:
                passage = json.loads(line)
                src = passage.get('source_document', 'Unknown')
                docs.add(src)
                if src not in doc_stats:
                    doc_stats[src] = 0
                doc_stats[src] += 1
                
                passages_count += 1
                text = passage.get('text', '')
                lengths.append(len(text.split()))
                for w in text.lower().split():
                    vocab.add(w)
                    
    # Write manifest
    manifest = {
        "documents": list(docs),
        "total_passages": passages_count,
        "vocabulary_size": len(vocab)
    }
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=4)
        
    print(f"Documents in Index: {len(docs)}")
    for d in docs:
        print(f" - {d} (Passages: {doc_stats[d]})")
        
    print(f"\nTotal Passages: {passages_count}")
    print(f"Vocabulary Size: {len(vocab)}")
    if lengths:
        print(f"Average Passage Length: {np.mean(lengths):.1f} words")
    else:
        print("Average Passage Length: 0 words")
        
    # Check for validation failures
    print("\n--- VALIDATION FAILURES ---")
    failures = {}
    if os.path.exists(failures_file):
        with open(failures_file, 'r', encoding='utf-8') as f:
            failures = json.load(f)
            
    if failures:
        for fname, msg in failures.items():
            print(f"[FAILED] {fname}: {msg}")
    else:
        print("No validation failures.")
        
    # Assertion: No document in the index should be in the failures list
    for d in docs:
        assert d not in failures, f"ASSERTION FAILED: Document {d} is in the index but failed validation!"
        
    expected_docs = {"CPA_2019.pdf", "Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021.pdf", "CONSUMER RIGHTS A2019-35.pdf", "E commerce rules_1732703966.pdf", "The Guidelines for Prevention and Regulation of Dark Patterns, 2023_1732707717.pdf", "Guidelines for Prevention of Misleading Advertisements & Endorsements for Mislaeding Advertisements, 2022.pdf"}
    
    # Very simple check
    if passages_count < 10:
        print("\nHEALTH CHECK: FAILED (Legal corpus not ready, < 10 passages)")
    elif len(docs) < 6:
        print("\nHEALTH CHECK: WARNING - Pilot Corpus (Missing full coverage)")
    else:
        print("\nHEALTH CHECK: OK - Full Corpus")

if __name__ == "__main__":
    main()
