import os
import glob
import json
import re

def split_legal_text(text, source_id, source_url="", extra_metadata=None):
    passages = []
    
    is_ecommerce = "E commerce" in source_id
    is_dark_patterns = "Dark Patterns" in source_id
    is_misleading = "Misleading" in source_id
    is_act = "A2019" in source_id or "CPA" in source_id
    
    doc_type = "Act" if is_act else "Rules" if ("Rules" in source_id or is_ecommerce) else "Guidelines"
    authority = "Central Consumer Protection Authority" if (is_dark_patterns or is_misleading) else "Central Government"
    date = "2019" if is_act else "2021" if "2021" in source_id else "2020" if is_ecommerce else "2022" if is_misleading else "2023"
    
    current_section = None
    buffer = []
    
    def flush_buffer(section_id, content, clause_id=None):
        if not content.strip() or len(content.split()) < 5:
            return
            
        passage_id = f"{source_id}_sec{section_id}" if section_id else f"{source_id}_p{len(passages)}"
        if clause_id:
            passage_id += f"_clause_{clause_id}"
            
        passage_obj = {
            "passage_id": passage_id,
            "source_document": source_id,
            "doc_type": doc_type,
            "authority": authority,
            "date": date,
            "section_or_rule": f"{section_id}({clause_id})" if clause_id else section_id,
            "url": source_url,
            "text": content.strip()
        }
        
        # Tagging superseded sections for CPA 2019
        if is_act:
            if section_id in ["34", "47", "58"]:
                passage_obj["tag"] = "pecuniary values superseded by Jurisdiction Rules, 2021"
                
        if extra_metadata:
            passage_obj.update(extra_metadata)
            
        passages.append(passage_obj)

    lines = text.split('\n')
    
    section_match = re.compile(r'^(\d+)\.\s+(.*)')
    clause_match = re.compile(r'^\((\d+|[a-z]+)\)\s+(.*)')
    annexure_match = re.compile(r'^Annexure\s*(\d+)?', re.IGNORECASE)
    
    current_section = "0"
    current_clause = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Match new section/rule/paragraph
        sm = section_match.match(line)
        am = annexure_match.match(line) if is_dark_patterns else None
        
        if sm:
            flush_buffer(current_section, " ".join(current_content), current_clause)
            current_section = sm.group(1)
            current_clause = None
            current_content = [line]
            continue
            
        if am:
            flush_buffer(current_section, " ".join(current_content), current_clause)
            current_section = "Annexure"
            current_clause = None
            current_content = [line]
            continue
            
        # Match clause if it's an Act (section 2 or 39), or E-Commerce (sub-rules), or Misleading (sub-clause for long sections)
        is_long_section = is_misleading and current_section in ["4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14"]
        if (is_act and current_section in ["2", "39"]) or is_ecommerce or is_long_section or (is_dark_patterns and current_section == "Annexure"):
            cm = clause_match.match(line)
            if cm:
                flush_buffer(current_section, " ".join(current_content), current_clause)
                current_clause = cm.group(1)
                current_content = [line]
                continue
                
        current_content.append(line)
        
    if current_content:
        flush_buffer(current_section, " ".join(current_content), current_clause)

    if len(passages) < 3 and len(text.split()) > 500:
        return split_into_paragraphs(text, source_id, source_url, extra_metadata)
        
    return passages

def split_into_paragraphs(text, source_id, source_url="", extra_metadata=None):
    paragraphs = re.split(r'\n\s*\n', text)
    passages = []
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if len(para.split()) < 10:
            continue
        passage_id = f"{source_id}_p{i}"
        passage_obj = {
            "passage_id": passage_id,
            "source_document": source_id,
            "url": source_url,
            "text": para
        }
        if extra_metadata:
            passage_obj.update(extra_metadata)
        passages.append(passage_obj)
    return passages

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    processed_dir = os.path.join(base_dir, 'data', 'processed')
    out_file = os.path.join(processed_dir, 'passages.jsonl')
    
    all_passages = []
    
    for filepath in glob.glob(os.path.join(processed_dir, '*.txt')):
        filename = os.path.basename(filepath)
        source_id = filename.replace('.txt', '')
        
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
            
        meta_path = os.path.join(processed_dir, f"{filename}.meta.json")
        extra_metadata = {}
        source_url = ""
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                source_url = meta.pop('url', '')
                extra_metadata = meta
                
        passages = split_legal_text(text, source_id, source_url, extra_metadata)
        all_passages.extend(passages)
        
    with open(out_file, 'w', encoding='utf-8') as f:
        for p in all_passages:
            f.write(json.dumps(p) + '\n')
            
    print(f"Created {len(all_passages)} passages and saved to {out_file}")

if __name__ == "__main__":
    main()
