import math

def precision_at_k(retrieved, relevant, k):
    retrieved_k = retrieved[:k]
    relevant_retrieved = [doc for doc in retrieved_k if doc in relevant]
    return len(relevant_retrieved) / k if k > 0 else 0.0

def recall_at_k(retrieved, relevant, k):
    if not relevant:
        return 0.0
    retrieved_k = retrieved[:k]
    relevant_retrieved = [doc for doc in retrieved_k if doc in relevant]
    return len(relevant_retrieved) / len(relevant)

def average_precision(retrieved, relevant):
    if not relevant:
        return 0.0
    hits = 0
    sum_precisions = 0.0
    for i, doc in enumerate(retrieved):
        if doc in relevant:
            hits += 1
            sum_precisions += hits / (i + 1)
    return sum_precisions / len(relevant)

def dcg_at_k(retrieved, graded_relevant, k):
    dcg = 0.0
    for i, doc in enumerate(retrieved[:k]):
        rel = graded_relevant.get(doc, 0)
        dcg += (2**rel - 1) / math.log2(i + 2)
    return dcg

def ndcg_at_k(retrieved, graded_relevant, k):
    if not graded_relevant:
        return 0.0
    ideal_retrieved = sorted(graded_relevant.keys(), key=lambda x: graded_relevant[x], reverse=True)
    idcg = dcg_at_k(ideal_retrieved, graded_relevant, k)
    if idcg == 0.0:
        return 0.0
    return dcg_at_k(retrieved, graded_relevant, k) / idcg
