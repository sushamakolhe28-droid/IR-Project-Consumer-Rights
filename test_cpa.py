import os
import re
import json
import glob

base_dir = r"c:\Users\kisho\OneDrive\Desktop\IR_Project_Consumer-Rights"
scratch_dir = os.path.join(base_dir, 'scratch')
raw_dir = os.path.join(base_dir, 'data', 'raw')

def get_cpa_passages():
    with open(os.path.join(scratch_dir, "CONSUMER RIGHTS A2019-35.pdf.txt"), "r", encoding="utf-8") as f:
        text = f.read()
    
    start_idx = text.find("BE it enacted by Parliament")
    if start_idx != -1:
        text = text[start_idx:]
    else:
        print("COULD NOT FIND 'BE it enacted by Parliament'")

    # Pre-clean
    text = re.sub(r'\bPage \d+ of \d+\b', '', text, flags=re.IGNORECASE)
    
    # Let's write a regex that matches section headings: "1. (1)", "3. (1)", etc.
    # Actually, section headings are like:
    # 1. (1) This Act may be called...
    # 2. In this Act, unless the context otherwise requires,—
    # (1) "advertisement" means...
    
    sections = {}
    
    # We will find the position of every section start: "\n1. ", "\n2. ", ... "\n107. "
    # Some might be "1. (1)".
    positions = []
    for i in range(1, 108):
        # search for \n{i}. 
        match = re.search(rf'\n{i}\.\s', text)
        if match:
            positions.append((i, match.start()))
        else:
            match = re.search(rf'^{i}\.\s', text, re.MULTILINE)
            if match:
                positions.append((i, match.start()))
            else:
                pass # print(f"Missing section {i}")
                
    positions.sort(key=lambda x: x[1])
    
    passages = []
    
    for idx, (sec_num, pos) in enumerate(positions):
        next_pos = positions[idx+1][1] if idx + 1 < len(positions) else len(text)
        sec_text = text[pos:next_pos].strip()
        
        if sec_num == 2:
            # Split Section 2
            # clauses (1) to (47)
            cl_positions = []
            for cl in range(1, 48):
                cl_match = re.search(rf'\n\({cl}\)\s', sec_text)
                if cl_match:
                    cl_positions.append((cl, cl_match.start()))
                else:
                    cl_match = re.search(rf'^\({cl}\)\s', sec_text, re.MULTILINE)
                    if cl_match:
                        cl_positions.append((cl, cl_match.start()))
                        
            cl_positions.sort(key=lambda x: x[1])
            lead_in = sec_text[:cl_positions[0][1]].strip() if cl_positions else ""
            
            for c_idx, (cl_num, c_pos) in enumerate(cl_positions):
                c_next = cl_positions[c_idx+1][1] if c_idx + 1 < len(cl_positions) else len(sec_text)
                cl_text = sec_text[c_pos:c_next].strip()
                
                if cl_num == 47:
                    # Split into i to ix
                    sub_positions = []
                    subclauses = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix']
                    for s in subclauses:
                        s_match = re.search(rf'\n\({s}\)\s', cl_text)
                        if s_match:
                            sub_positions.append((s, s_match.start()))
                        else:
                            s_match = re.search(rf'^\({s}\)\s', cl_text, re.MULTILINE)
                            if s_match:
                                sub_positions.append((s, s_match.start()))
                    
                    sub_positions.sort(key=lambda x: x[1])
                    cl_lead_in = cl_text[:sub_positions[0][1]].strip() if sub_positions else ""
                    
                    for s_idx, (s_num, s_pos) in enumerate(sub_positions):
                        s_next = sub_positions[s_idx+1][1] if s_idx + 1 < len(sub_positions) else len(cl_text)
                        s_text = cl_text[s_pos:s_next].strip()
                        
                        full_text = f"{lead_in} {cl_lead_in} {s_text}"
                        passages.append({
                            "passage_id": f"CPA_s2_{cl_num}_{s_num}",
                            "text": full_text
                        })
                else:
                    full_text = f"{lead_in} {cl_text}"
                    passages.append({
                        "passage_id": f"CPA_s2_{cl_num}",
                        "text": full_text
                    })
        else:
            p_id = f"CPA_s{sec_num}"
            passages.append({
                "passage_id": p_id,
                "text": sec_text
            })
            
    # Post-process tags
    for p in passages:
        if p["passage_id"] in ["CPA_s34", "CPA_s47", "CPA_s58"]:
            p["text"] += " superseded by Jurisdiction Rules 2021"
            
    return passages

print(len(get_cpa_passages()))
