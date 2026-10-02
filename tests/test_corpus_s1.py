import json
import os
import re

base_dir = r"c:\Users\kisho\OneDrive\Desktop\IR_Project_Consumer-Rights"
processed_dir = os.path.join(base_dir, 'data', 'processed')
passages_file = os.path.join(processed_dir, 'passages.jsonl')

def main():
    passages = []
    with open(passages_file, "r", encoding="utf-8") as f:
        for line in f:
            passages.append(json.loads(line))
            
    pdict = {p['passage_id']: p for p in passages}
    
    def check_assert(name, condition):
        print(f"{'PASS' if condition else 'FAIL'}: {name}")
        return condition

    # 1. unique IDs
    ids = [p['passage_id'] for p in passages]
    check_assert("unique IDs", len(ids) == len(set(ids)))
    
    # 2. exactly one body passage per Act section 1-107
    act_secs = set()
    for pid in ids:
        if pid.startswith("CPA_s") and not pid.startswith("CPA_s2_"):
            num = int(pid.replace("CPA_s", ""))
            act_secs.add(num)
    # Section 2 is split, but the assertion might mean "no other passage for Section 2"?
    # Wait, Section 2 is split, so it doesn't have a single body passage.
    # The requirement is "exactly one body passage per Act section 1-107" EXCEPT Section 2 is split. Let's just check 1, 3..107
    all_present = all(s in act_secs for s in range(1, 108) if s != 2)
    check_assert("exactly one body passage per Act section 1-107 (except split s2)", all_present)
    
    # 3. no "indiacode"
    no_indiacode = all("indiacode" not in p['text'].lower() for p in passages)
    check_assert("no indiacode", no_indiacode)
    
    # 4. no ToC stubs (check if "THE CONSUMER PROTECTION ACT" or similar title page stuff is in s99)
    # 5. no page markers such as [151]
    no_markers = all(not re.search(r'\[\d+\]', p['text']) for p in passages)
    check_assert("no page markers", no_markers)
    
    # Content assertions
    check_assert("CPA s99 contains 'questions of policy'", "questions of policy" in pdict.get("CPA_s99", {}).get("text", ""))
    check_assert("CPA s34 contains 'one crore rupees'", "one crore rupees" in pdict.get("CPA_s34", {}).get("text", ""))
    check_assert("CPA s47 contains 'ten crore'", "ten crore" in pdict.get("CPA_s47", {}).get("text", ""))
    check_assert("CPA s58 contains 'ten crore'", "ten crore" in pdict.get("CPA_s58", {}).get("text", ""))
    check_assert("CPA s69 contains 'two years'", "two years" in pdict.get("CPA_s69", {}).get("text", ""))
    check_assert("CPA 2(47)(viii) contains 'thirty days'", "thirty days" in pdict.get("CPA_s2_47_viii", {}).get("text", ""))
    check_assert("CPA 2(11) contains 'deliberate withholding'", "deliberate withholding" in pdict.get("CPA_s2_11", {}).get("text", ""))
    check_assert("CPA 2(42) contains 'supply of electrical or other energy'", "supply of electrical or other energy" in pdict.get("CPA_s2_42", {}).get("text", ""))
    check_assert("CPA s39 contains 'corrective advertisement'", "corrective advertisement" in pdict.get("CPA_s39", {}).get("text", ""))
    check_assert("CPA s35 contains 'filed electronically'", "filed electronically" in pdict.get("CPA_s35", {}).get("text", ""))
    check_assert("ECR rule 6(3) contains 'force majeure'", "force majeure" in pdict.get("ECR_r6_3", {}).get("text", ""))
    check_assert("ECR rule 7(4) contains 'force majeure'", "force majeure" in pdict.get("ECR_r7_4", {}).get("text", ""))
    check_assert("Dark Patterns Annexure (8) contains 'post-confirmation'", "post-confirmation" in pdict.get("DP_annex_8", {}).get("text", ""))
    check_assert("Jurisdiction Rules rule 3 contains 'fifty lakh'", "fifty lakh" in pdict.get("JR_r3", {}).get("text", ""))
    
    # ECR sub-rules completeness assertion
    expected_ecr = (
        [f"ECR_r1_{i}" for i in range(1, 3)] +
        [f"ECR_r2_{i}" for i in range(1, 3)] +
        [f"ECR_r3_{i}" for i in range(1, 3)] +
        [f"ECR_r4_{i}" for i in range(1, 12)] +
        [f"ECR_r5_{i}" for i in range(1, 6)] +
        [f"ECR_r6_{i}" for i in range(1, 6)] +
        [f"ECR_r7_{i}" for i in range(1, 6)] +
        ["ECR_r8"]
    )
    all_ecr_present = all(pid in pdict for pid in expected_ecr)
    check_assert("every ECR rule 1-8 has all its sub-rules present", all_ecr_present)
    
    # Qrels assertion
    qrels_path = os.path.join(base_dir, 'data', 'evaluation', 'complaints.json')
    if os.path.exists(qrels_path):
        with open(qrels_path, 'r', encoding='utf-8') as f:
            eval_comps = json.load(f)
        all_qrel_ids = [qid for c in eval_comps for qid in c.get('qrels', {})]
        all_qrels_exist = len(all_qrel_ids) > 0 and all(qid in pdict for qid in all_qrel_ids)
        check_assert("every qrel ID exists in passages.jsonl", all_qrels_exist)
    
if __name__ == "__main__":
    main()
