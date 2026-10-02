import os, json
from src.preprocess import preprocess
from src.ie import extract_entities
from src.recommender import Recommender

class MockIndex:
    def __init__(self):
        pass

base_dir = r'c:\Users\kisho\OneDrive\Desktop\IR_Project_Consumer-Rights'
ontology_path = os.path.join(base_dir, 'src', 'ontology.json')

with open(ontology_path, 'r', encoding='utf-8') as f:
    ontology = json.load(f)

recommender = Recommender(MockIndex(), None, ontology_path)

tests = [
    "I got soap instead of the mobile phone I ordered.",
    "They sent me a completely different item.",
    "My washing machine stopped working after I received it.",
    "The seller refuses to return my money.",
    "I keep paying for internet but the connection barely works.",
    "The electricity service keeps going off even though I pay my bills.",
    "The price they charged me was higher than the price displayed.",
    "The advertisement promised features that the product doesn't actually have.",
    "The company charged me for something I never agreed to.",
    "The product arrived broken."
]

for i, test in enumerate(tests, 1):
    print(f"\n--- TEST {i} ---")
    print(f"Complaint: {test}")
    facts = extract_entities(test)
    print(f"Extracted Facts: {facts}")
    tokens = preprocess(test)
    print(f"IR Query Tokens: {tokens}")
    predicted = recommender.get_fraud_prediction(tokens, test)
    print(f"Classification Result: {predicted}")
    recommendations = recommender.knowledge_based_recommendation(predicted, facts.get('amount'))
    if recommendations:
        rec = recommendations[0]
        print(f"Mapped Rights: {rec.get('violated_rights')}")
        print(f"Legal Mapping: {rec.get('relevant_laws')}")
    else:
        print("Mapped Rights: None (Uncertain classification)")
        print("Legal Mapping: None")
