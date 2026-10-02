import re
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = None

def extract_amount(text):
    # Matches Rs, ₹, रुपये, lakh, crore
    pattern = r'(?:rs\.?|inr|₹|रुपये)\s*([\d,]+(?:(?:\.|,)\d+)?)\s*(lakh|crore)?|\b([\d,]+(?:(?:\.|,)\d+)?)\s*(lakh|crore)?\s*(?:rupees|rs\.?|रुपये)\b'
    matches = re.findall(pattern, text, re.IGNORECASE)
    amounts = []
    for match in matches:
        amt_str = match[0] if match[0] else match[2]
        modifier = match[1].lower() if match[1] else (match[3].lower() if match[3] else "")
        
        amt_str = amt_str.replace(',', '')
        try:
            amt = float(amt_str)
            if modifier == 'lakh':
                amt *= 100000
            elif modifier == 'crore':
                amt *= 10000000
            amounts.append(int(amt))
        except:
            pass
    return max(amounts) if amounts else None

def extract_platform(text):
    platforms = ['amazon', 'flipkart', 'meesho', 'myntra', 'zomato', 'swiggy', 'uber', 'ola', 'blinkit', 'zepto']
    for p in platforms:
        if re.search(r'\b' + p + r'\b', text, re.IGNORECASE):
            return p.capitalize()
    return None

def extract_items(text):
    # Pattern: ordered X but received Y
    expected = None
    received = None
    
    match = re.search(r'ordered\s+(.*?)\s+(?:but|and)\s+received\s+(.*?)(?=\s+(?:from|on|for|at)|[.,\n]|$)', text, re.IGNORECASE)
    if match:
        expected = match.group(1).strip()
        received = match.group(2).strip()
        
    return expected, received

def extract_dates(text):
    dates = []
    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == 'DATE':
                dates.append(ent.text)
    return dates

def extract_refund_status(text):
    text_lower = text.lower()
    if 'refunded' in text_lower or 'got refund' in text_lower:
        return 'refunded'
    elif 'refused refund' in text_lower or 'won\'t refund' in text_lower or 'no refund' in text_lower:
        return 'refused'
    elif 'pending' in text_lower and 'refund' in text_lower:
        return 'pending'
    return None

def extract_entities(text):
    expected, received = extract_items(text)
    
    extracted = {
        'amount': extract_amount(text),
        'seller_platform': extract_platform(text),
        'dates': extract_dates(text),
        'expected_item': expected,
        'received_item': received,
        'refund_status': extract_refund_status(text),
        'problem': None, # Placeholder for more complex dependency logic
        'action_taken': None # Placeholder
    }
    
    return extracted

if __name__ == "__main__":
    sample = "I ordered a phone from Amazon on 15th August for ₹ 1.5 lakh using UPI but received a brick. They refused refund."
    print("Extracting from:", sample)
    print(extract_entities(sample))
