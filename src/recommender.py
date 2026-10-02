import json
import os
import numpy as np

class Recommender:
    def __init__(self, index_obj, ranker, ontology_path):
        self.index_obj = index_obj
        self.ranker = ranker
        
        with open(ontology_path, 'r', encoding='utf-8') as f:
            self.ontology = json.load(f)
            
        # Decision: Using a multilingual model ('paraphrase-multilingual-MiniLM-L12-v2') 
        # instead of English-only because we need to support Hindi, Marathi, etc. (per audio inputs) 
        # and Hinglish without relying on a separate translation layer.
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # Representative examples per category
        self.categories = {
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
        
        # Precompute embeddings for categories
        self.cat_embeddings = {}
        for cat, examples in self.categories.items():
            self.cat_embeddings[cat] = self.model.encode(examples)
            
    def get_fraud_prediction(self, query_tokens, text):
        query_emb = self.model.encode([text])[0]
        
        scores = {}
        for cat, embs in self.cat_embeddings.items():
            # Use max similarity among examples for this category
            sims = np.dot(embs, query_emb) / (np.linalg.norm(embs, axis=1) * np.linalg.norm(query_emb))
            scores[cat] = np.max(sims)
            
        # Sort categories by score
        sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top1_cat, top1_score = sorted_cats[0]
        top2_cat, top2_score = sorted_cats[1]
        
        margin = top1_score - top2_score
        
        # Thresholds tuned from validation script (src/validate_thresholds.py)
        # Using placeholder values here, should be tuned
        SCORE_THRESHOLD = 0.50
        MARGIN_THRESHOLD = 0.05
        
        if top1_cat == "other" or top1_score < SCORE_THRESHOLD or margin < MARGIN_THRESHOLD:
            return [] # Uncertain / Not a consumer complaint
            
        return [top1_cat]
        
    def knowledge_based_recommendation(self, predicted_frauds, amount=None):
        recommendations = []
        
        # Determine jurisdiction based on amount
        jurisdiction = "District Consumer Commission (up to 50 Lakhs)"
        if amount:
            if amount > 20000000:
                jurisdiction = "National Consumer Disputes Redressal Commission (above 2 Crores)"
            elif amount > 5000000:
                jurisdiction = "State Consumer Disputes Redressal Commission (50 Lakhs to 2 Crores)"
                
        for fraud in predicted_frauds:
            # Map standard category to ontology if needed. Some categories match exactly.
            mapped_fraud = fraud
            if fraud == "non-delivery": mapped_fraud = "non-delivery"
            # In ontology.json, we have 'defective goods', 'non-delivery', 'misleading advertisement', etc.
            
            if mapped_fraud in self.ontology.get('fraud_types', {}):
                data = self.ontology['fraud_types'][mapped_fraud]
                forum = data['forum']
                
                if forum == "Consumer Commission":
                    forum = f"{forum} -> {jurisdiction}"
                    
                rec = {
                    "fraud_type": mapped_fraud,
                    "violated_rights": data['violated_rights'],
                    "relevant_laws": data['law_sections'],
                    "where_to_complain": forum,
                    "action": data['action_suggested']
                }
                recommendations.append(rec)
                
        return recommendations
