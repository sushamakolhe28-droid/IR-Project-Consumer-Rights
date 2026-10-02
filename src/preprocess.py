import re
import json
import os
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

nltk.download('stopwords', quiet=True)

stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

HINGLISH_MAP = {
    "paisa wapas": "refund",
    "dhokha": "fraud",
    "faraud": "fraud",
    "thagi": "scam",
    "kharab": "defective",
    "tuta hua": "broken",
    "wapas": "return",
    "chori": "theft",
    "nakli": "fake",
    "jhooth": "lie",
    "jhootha": "false",
    "galat": "wrong"
}

def normalize_hinglish(text):
    text = text.replace("paisa wapas", "refund")
    text = text.replace("tuta hua", "broken")
    tokens = text.split()
    normalized = [HINGLISH_MAP.get(t, t) for t in tokens]
    return " ".join(normalized)

def preprocess(text):
    text = text.lower()
    text = normalize_hinglish(text)
    tokens = re.findall(r'\b[a-z0-9]+\b', text)
    return [stemmer.stem(t) for t in tokens if t not in stop_words]

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    processed_dir = os.path.join(base_dir, 'data', 'processed')
    in_file = os.path.join(processed_dir, 'passages.jsonl')
    out_file = os.path.join(processed_dir, 'passages_preprocessed.jsonl')
    
    if not os.path.exists(in_file):
        print(f"Error: {in_file} not found. Run s1_fixes.py first.")
        return
        
    processed_count = 0
    with open(in_file, 'r', encoding='utf-8') as f_in, open(out_file, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            passage = json.loads(line)
            breadcrumb = passage.get('metadata', {}).get('breadcrumb', '')
            text_to_index = f"{breadcrumb} {passage['text']}" if breadcrumb else passage['text']
            tokens = preprocess(text_to_index)
            passage['tokens'] = tokens
            f_out.write(json.dumps(passage) + '\n')
            processed_count += 1
            
    print(f"Preprocessed {processed_count} passages and saved to {out_file}")

if __name__ == "__main__":
    main()
