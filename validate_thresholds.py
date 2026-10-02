import os
import numpy as np
from sentence_transformers import SentenceTransformer

print("Loading model (paraphrase-multilingual-MiniLM-L12-v2)...")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

categories = {
    "defective goods": [
        "The product I received is damaged and broken.",
        "My phone screen stopped working after two days.",
        "Quality of the item is very poor and defective."
    ],
    "non-delivery": [
        "I ordered a laptop but it never arrived.",
        "Received an empty box instead of the product.",
        "Wrong item delivered, not what I ordered."
    ],
    "deficiency in service": [
        "The internet connection is constantly dropping.",
        "Customer support was extremely rude and unhelpful.",
        "The flight was delayed by 10 hours without notice."
    ],
    "unfair trade practice": [
        "They charged me hidden fees that were not mentioned.",
        "The seller forced me to buy an extended warranty.",
        "The MRP on the product was altered with a sticker."
    ],
    "refund / redressal refusal": [
        "They are refusing to give me my money back.",
        "The seller denied the return request without reason.",
        "My refund has been pending for over a month."
    ],
    "misleading advertisement": [
        "The ad promised a free gift which was a lie.",
        "The product looks completely different from the pictures.",
        "False claims about weight loss in the advertisement."
    ],
    "other": [
        "I want to complain about my neighbor's dog.",
        "The weather today is terrible.",
        "How do I cook pasta?",
        "My friend owes me money."
    ]
}

cat_embeddings = {}
for cat, examples in categories.items():
    cat_embeddings[cat] = model.encode(examples)

tests = [
    # Representative
    "I bought a TV but the screen is cracked.",
    "Order #123 was supposed to arrive last week but hasn't.",
    "The airline lost my luggage and won't compensate me.",
    "I was charged for a subscription I explicitly cancelled.",
    # Ambiguous
    "I hate this product it is so stupid.",
    "My internet is slow sometimes.",
    # Unrelated
    "Where is the nearest hospital?",
    "How do I file taxes?",
    "My wife and I are having a dispute."
]

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

print("\n--- SEMANTIC THRESHOLD VALIDATION ---")
for test in tests:
    print(f"\nComplaint: '{test}'")
    query_emb = model.encode([test])[0]
    
    scores = {}
    for cat, embs in cat_embeddings.items():
        sims = [cosine_similarity(query_emb, e) for e in embs]
        scores[cat] = max(sims)
        
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top1_cat, top1_score = sorted_scores[0]
    top2_cat, top2_score = sorted_scores[1]
    margin = top1_score - top2_score
    
    print("Scores:")
    for cat, sim in sorted_scores:
        print(f"  {sim:.4f} -> {cat}")
        
    print(f"Top 1: {top1_cat} ({top1_score:.4f}), Margin to Top 2: {margin:.4f}")

