import json
import os
import sys
import math
import csv
from collections import defaultdict, Counter

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from src.index import InvertedIndex
from src.preprocess import preprocess
from src.rankers.tfidf import TFIDFRanker
from src.rankers.bm25 import BM25Ranker
from src.rankers.language_model import LanguageModelRanker
from src.query_expansion import expand_query

def precision_at_k(retrieved, relevant, k=5):
    if k == 0: return 0.0
    top_k = retrieved[:k]
    hits = sum(1 for d in top_k if d in relevant)
    return hits / k

def recall_at_k(retrieved, relevant, k=10):
    if not relevant: return 0.0
    top_k = retrieved[:k]
    hits = sum(1 for d in top_k if d in relevant)
    return hits / len(relevant)

def average_precision(retrieved, relevant):
    if not relevant: return 0.0
    hits = 0.0
    sum_prec = 0.0
    for i, doc in enumerate(retrieved):
        if doc in relevant:
            hits += 1.0
            sum_prec += hits / (i + 1)
    return sum_prec / len(relevant)

def dcg_at_k(retrieved, qrels_dict, k=10):
    dcg = 0.0
    for i, doc in enumerate(retrieved[:k]):
        if doc in qrels_dict:
            grade = qrels_dict[doc]
            dcg += (2**grade - 1) / math.log2(i + 2)
    return dcg

def ndcg_at_k(retrieved, qrels_dict, k=10):
    if not qrels_dict: return 0.0
    actual = dcg_at_k(retrieved, qrels_dict, k)
    ideal_docs = sorted(qrels_dict.keys(), key=lambda d: qrels_dict[d], reverse=True)
    ideal = dcg_at_k(ideal_docs, qrels_dict, k)
    if ideal == 0.0: return 0.0
    return actual / ideal

def evaluate_subset(model, query_list, is_hindi_zero_token=False, use_expansion=False):
    if not query_list:
        return {'P@5': 0.0, 'R@10': 0.0, 'MAP': 0.0, 'nDCG@10': 0.0, 'count': 0}
        
    if is_hindi_zero_token:
        # By construction: Hindi produces zero tokens in English lexical index
        return {'P@5': 0.0, 'R@10': 0.0, 'MAP': 0.0, 'nDCG@10': 0.0, 'count': len(query_list)}
        
    p5_list, r10_list, map_list, ndcg_list = [], [], [], []
    for c in query_list:
        qrels = c.get('qrels', {})
        relevant_docs = set(qrels.keys())
        
        if c.get('lang') == 'hi':
            # Hindi queries produce zero tokens by construction
            p5_list.append(0.0)
            r10_list.append(0.0)
            map_list.append(0.0)
            ndcg_list.append(0.0)
            continue
            
        base_tokens = preprocess(c['text'])
        if use_expansion:
            tokens = expand_query(c['text'], user_tokens=base_tokens)
        else:
            tokens = base_tokens
            
        if not tokens:
            retrieved = []
        else:
            scored = model.score(tokens)
            retrieved = [doc_id for doc_id, score in scored]
            
        p5_list.append(precision_at_k(retrieved, relevant_docs, 5))
        r10_list.append(recall_at_k(retrieved, relevant_docs, 10))
        map_list.append(average_precision(retrieved, relevant_docs))
        ndcg_list.append(ndcg_at_k(retrieved, qrels, 10))
        
    return {
        'P@5': sum(p5_list) / len(p5_list),
        'R@10': sum(r10_list) / len(r10_list),
        'MAP': sum(map_list) / len(map_list),
        'nDCG@10': sum(ndcg_list) / len(ndcg_list),
        'count': len(query_list)
    }

def run_ablation(index_obj=None, complaints=None, save=True):
    index_path = os.path.join(base_dir, 'data', 'processed', 'index.pkl')
    complaints_path = os.path.join(base_dir, 'data', 'evaluation', 'complaints.json')
    results_dir = os.path.join(base_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    if index_obj is None:
        if not os.path.exists(index_path):
            print(f"Error: {index_path} not found. Run index.py first.")
            return None
        index_obj = InvertedIndex.load(index_path)
        
    if complaints is None:
        with open(complaints_path, 'r', encoding='utf-8') as f:
            complaints = json.load(f)
            
    bm25 = BM25Ranker(index_obj, k1=1.5, b=0.75)
    
    unrelated_queries = [c for c in complaints if not c.get('qrels') or c.get('category') in ['Out-of-Scope', 'Ambiguous']]
    dev_eval = [c for c in complaints if c['split'] == 'dev' and c not in unrelated_queries]
    test_eval = [c for c in complaints if c['split'] == 'test' and c not in unrelated_queries]
    
    dev_eval_no_terms = [c for c in dev_eval if not c.get('uses_corpus_terms')]
    test_eval_no_terms = [c for c in test_eval if not c.get('uses_corpus_terms')]
    
    dev_en = [c for c in dev_eval if c['lang'] == 'en']
    dev_hien = [c for c in dev_eval if c['lang'] == 'hi-en']
    dev_hi = [c for c in dev_eval if c['lang'] == 'hi']
    
    test_en = [c for c in test_eval if c['lang'] == 'en']
    test_hien = [c for c in test_eval if c['lang'] == 'hi-en']
    test_hi = [c for c in test_eval if c['lang'] == 'hi']
    
    subsets_spec = [
        ('Dev (All Evaluable)', dev_eval, False),
        ('Dev (Excl. Corpus Terms)', dev_eval_no_terms, False),
        ('Dev (English)', dev_en, False),
        ('Dev (Hinglish)', dev_hien, False),
        ('Dev (Hindi - Zero Tokens)', dev_hi, True),
        ('Test (All Evaluable)', test_eval, False),
        ('Test (Excl. Corpus Terms)', test_eval_no_terms, False),
        ('Test (English)', test_en, False),
        ('Test (Hinglish)', test_hien, False),
        ('Test (Hindi - Zero Tokens)', test_hi, True),
    ]
    
    ablation_json = {
        'BM25_No_Expansion': {},
        'BM25_With_Expansion': {}
    }
    csv_rows = []
    
    print("\n" + "=" * 105)
    print("QUERY EXPANSION ABLATION: BM25 WITHOUT VS WITH EXPANSION")
    print("Note: All numbers marked 'qrels pending human verification'")
    print("=" * 105)
    print(f"{'Subset':<28} | {'Config':<18} | {'N':<3} | {'P@5':<7} | {'R@10':<7} | {'MAP':<7} | {'nDCG@10':<7} | {'Delta MAP'}")
    print("-" * 105)
    
    for subset_name, qset, is_hi in subsets_spec:
        res_no = evaluate_subset(bm25, qset, is_hindi_zero_token=is_hi, use_expansion=False)
        res_no['note'] = "qrels pending human verification"
        ablation_json['BM25_No_Expansion'][subset_name] = res_no
        
        res_ex = evaluate_subset(bm25, qset, is_hindi_zero_token=is_hi, use_expansion=True)
        res_ex['note'] = "qrels pending human verification"
        ablation_json['BM25_With_Expansion'][subset_name] = res_ex
        
        d_map = res_ex['MAP'] - res_no['MAP']
        d_str = f"{d_map:+.4f}" if not is_hi else "0.0000"
        
        print(f"{subset_name:<28} | {'No Expansion':<18} | {res_no['count']:<3} | {res_no['P@5']:.4f}  | {res_no['R@10']:.4f}  | {res_no['MAP']:.4f}  | {res_no['nDCG@10']:.4f}   | -")
        print(f"{subset_name:<28} | {'With Expansion':<18} | {res_ex['count']:<3} | {res_ex['P@5']:.4f}  | {res_ex['R@10']:.4f}  | {res_ex['MAP']:.4f}  | {res_ex['nDCG@10']:.4f}   | {d_str}")
        print("-" * 105)
        
        csv_rows.append({
            'model': 'BM25',
            'expansion': 'No',
            'subset': subset_name,
            'count': res_no['count'],
            'P@5': round(res_no['P@5'], 4),
            'R@10': round(res_no['R@10'], 4),
            'MAP': round(res_no['MAP'], 4),
            'nDCG@10': round(res_no['nDCG@10'], 4),
            'note': "qrels pending human verification"
        })
        csv_rows.append({
            'model': 'BM25',
            'expansion': 'Yes',
            'subset': subset_name,
            'count': res_ex['count'],
            'P@5': round(res_ex['P@5'], 4),
            'R@10': round(res_ex['R@10'], 4),
            'MAP': round(res_ex['MAP'], 4),
            'nDCG@10': round(res_ex['nDCG@10'], 4),
            'note': "qrels pending human verification"
        })
        
    if save:
        json_path = os.path.join(results_dir, 'ablation.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(ablation_json, f, indent=2)
        print(f"\nSaved ablation results to {json_path}")
        
        csv_path = os.path.join(results_dir, 'ablation.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['model', 'expansion', 'subset', 'count', 'P@5', 'R@10', 'MAP', 'nDCG@10', 'note']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)
        print(f"Saved ablation results to {csv_path}")
        
    return ablation_json

def main():
    index_path = os.path.join(base_dir, 'data', 'processed', 'index.pkl')
    complaints_path = os.path.join(base_dir, 'data', 'evaluation', 'complaints.json')
    results_dir = os.path.join(base_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    if not os.path.exists(index_path):
        print(f"Error: {index_path} not found. Run index.py first.")
        return
        
    index_obj = InvertedIndex.load(index_path)
    
    models = {
        'TF-IDF': TFIDFRanker(index_obj),
        'BM25': BM25Ranker(index_obj, k1=1.5, b=0.75),
        'QL-Dirichlet': LanguageModelRanker(index_obj, smoothing='dirichlet', mu=1000),
        'QL-Jelinek-Mercer': LanguageModelRanker(index_obj, smoothing='jm', lambda_jm=0.5)
    }
    
    with open(complaints_path, 'r', encoding='utf-8') as f:
        complaints = json.load(f)
        
    # Unrelated queries (excluded from averages)
    unrelated_queries = [c for c in complaints if not c.get('qrels') or c.get('category') in ['Out-of-Scope', 'Ambiguous']]
    dev_unrelated = [c for c in unrelated_queries if c['split'] == 'dev' and c not in unrelated_queries]
    test_unrelated = [c for c in unrelated_queries if c['split'] == 'test' and c not in unrelated_queries]
    
    # Evaluable queries
    dev_eval = [c for c in complaints if c['split'] == 'dev' and c not in unrelated_queries]
    test_eval = [c for c in complaints if c['split'] == 'test' and c not in unrelated_queries]
    
    # Excluding queries with corpus terms
    dev_eval_no_terms = [c for c in dev_eval if not c.get('uses_corpus_terms')]
    test_eval_no_terms = [c for c in test_eval if not c.get('uses_corpus_terms')]
    
    # Language splits
    dev_en = [c for c in dev_eval if c['lang'] == 'en']
    dev_hien = [c for c in dev_eval if c['lang'] == 'hi-en']
    dev_hi = [c for c in dev_eval if c['lang'] == 'hi']
    
    test_en = [c for c in test_eval if c['lang'] == 'en']
    test_hien = [c for c in test_eval if c['lang'] == 'hi-en']
    test_hi = [c for c in test_eval if c['lang'] == 'hi']
    
    subsets_spec = [
        ('Dev (All Evaluable)', dev_eval, False),
        ('Dev (Excl. Corpus Terms)', dev_eval_no_terms, False),
        ('Dev (English)', dev_en, False),
        ('Dev (Hinglish)', dev_hien, False),
        ('Dev (Hindi - Zero Tokens)', dev_hi, True),
        ('Test (All Evaluable)', test_eval, False),
        ('Test (Excl. Corpus Terms)', test_eval_no_terms, False),
        ('Test (English)', test_en, False),
        ('Test (Hinglish)', test_hien, False),
        ('Test (Hindi - Zero Tokens)', test_hi, True),
    ]
    
    all_metrics = {}
    csv_rows = []
    
    print("=" * 95)
    print("CONSUMER RIGHTS IR RETRIEVAL BENCHMARK EVALUATION")
    print("Note: All numbers marked 'qrels pending human verification'")
    print(f"Total queries: {len(complaints)} | Total Unrelated/Ambiguous excluded: {len(unrelated_queries)}")
    print("=" * 95)
    
    for model_name, model in models.items():
        all_metrics[model_name] = {}
        print(f"\n--- MODEL: {model_name} ---")
        print(f"{'Subset':<28} | {'N':<3} | {'P@5':<7} | {'R@10':<7} | {'MAP':<7} | {'nDCG@10':<7} | {'Status'}")
        print("-" * 95)
        for subset_name, qset, is_hi in subsets_spec:
            res = evaluate_subset(model, qset, is_hindi_zero_token=is_hi, use_expansion=False)
            res['note'] = "qrels pending human verification"
            if is_hi:
                res['limitation'] = "vocabulary-mismatch limitation (Devanagari deleted by [a-z0-9] analyzer, score 0 by construction, no translation)"
            all_metrics[model_name][subset_name] = res
            
            status = "0 by construction" if is_hi else "evaluated"
            print(f"{subset_name:<28} | {res['count']:<3} | {res['P@5']:.4f}  | {res['R@10']:.4f}  | {res['MAP']:.4f}  | {res['nDCG@10']:.4f}   | {status}")
            
            csv_rows.append({
                'model': model_name,
                'subset': subset_name,
                'count': res['count'],
                'P@5': round(res['P@5'], 4),
                'R@10': round(res['R@10'], 4),
                'MAP': round(res['MAP'], 4),
                'nDCG@10': round(res['nDCG@10'], 4),
                'note': res['note']
            })
            
    # Save results to json
    json_path = os.path.join(results_dir, 'metrics.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_metrics, f, indent=2)
    print(f"\nSaved metrics to {json_path}")
    
    # Save results to csv
    csv_path = os.path.join(results_dir, 'metrics.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['model', 'subset', 'count', 'P@5', 'R@10', 'MAP', 'nDCG@10', 'note']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"Saved metrics to {csv_path}")
    
    # Run ablation
    run_ablation(index_obj=index_obj, complaints=complaints, save=True)

if __name__ == "__main__":
    main()
