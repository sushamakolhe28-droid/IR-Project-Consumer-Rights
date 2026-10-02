# Consumer Rights Legal Information Retrieval System

## Problem Statement
Consumers often do not know their rights or where to file; the system takes a complaint in plain language and returns the relevant provisions of Indian consumer law, the forum (when an amount is given) and the filing deadline.

---

## Legal Corpus Statistics
The legal corpus is extracted directly from official Indian legal gazettes and publications stored in `data/raw/` and segmented into 232 legal passages (`data/processed/passages.jsonl`):

1. **Consumer Protection Act, 2019** (`CONSUMER RIGHTS A2019-35.pdf`): 161 passages (106 individual section body passages, 46 Section 2 clause passages, 9 Section 2(47) sub-clause passages).
2. **Consumer Protection (E-Commerce) Rules, 2020** (`E commerce rules_1732703966.pdf`): 33 sub-rule passages across Rules 1–8.
3. **Guidelines for Prevention and Regulation of Dark Patterns, 2023** (`The Guidelines for Prevention and Regulation of Dark Patterns, 2023_1732707717.pdf`): 20 passages (7 paragraph provisions and 13 Annexure 1 dark pattern definitions).
4. **Consumer Protection (Jurisdiction Rules), 2021** (`Consumer Protection (Jurisdiction of the District Commission... Rules, 2021.pdf`): 3 passages (Rules 3, 4, and 5 for pecuniary jurisdiction).
5. **Guidelines for Prevention of Misleading Advertisements, 2022** (`Misleading_Ads_Guidelines_2022_OCR.txt`): 15 section passages.

- **Total Corpus Size:** 232 legal passages
- **Inverted Index Vocabulary:** 2,752 unique stemmed terms across 28,114 total token occurrences (`data/processed/index.pkl`)

---

## Retrieval Models
The engine implements four lexical ranking functions from scratch:
- **BM25 (Best Matching 25):** Probabilistic ranking function with non-linear term frequency saturation ($k_1=1.5$) and document length normalization ($b=0.75$). Default model.
- **TF-IDF:** Classic vector-space weighting combining log-scaled inverse document frequency with length-normalized term frequency.
- **Query Likelihood (Dirichlet Smoothing):** Language model ranking computing document generation probability smoothed using Bayesian Dirichlet prior ($\mu=1000$).
- **Query Likelihood (Jelinek-Mercer Smoothing):** Language model ranking utilizing linear interpolation between document model and collection background model ($\lambda=0.5$).

---

## Evaluation Benchmark Results
> **Note:** All metrics are **preliminary, qrels pending human verification**. Unrelated/ambiguous queries (6 total: 3 Dev, 3 Test) are excluded from performance averages.

The metrics below are loaded directly from `results/metrics.json`:

| Model | Evaluation Subset | N | P@5 | R@10 | MAP | nDCG@10 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| TF-IDF | Dev (All Evaluable) | 17 | 0.0941 | 0.2206 | 0.1790 | 0.2739 |
| TF-IDF | Dev (Excl. Corpus Terms) | 15 | 0.0933 | 0.2278 | 0.1772 | 0.2620 |
| TF-IDF | Dev (English) | 7 | 0.1714 | 0.4048 | 0.2943 | 0.4332 |
| TF-IDF | Dev (Hinglish) | 4 | 0.1000 | 0.2292 | 0.2457 | 0.4060 |
| TF-IDF | Dev (Hindi - Zero Tokens) | 6 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| TF-IDF | Test (All Evaluable) | 17 | 0.1294 | 0.2647 | 0.2134 | 0.3844 |
| TF-IDF | Test (Excl. Corpus Terms) | 13 | 0.0923 | 0.1923 | 0.1454 | 0.2642 |
| TF-IDF | Test (English) | 6 | 0.1667 | 0.3611 | 0.2842 | 0.5120 |
| TF-IDF | Test (Hinglish) | 6 | 0.2000 | 0.3889 | 0.3206 | 0.5771 |
| TF-IDF | Test (Hindi - Zero Tokens) | 5 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| BM25 | Dev (All Evaluable) | 17 | 0.1529 | 0.2892 | 0.2286 | 0.3438 |
| BM25 | Dev (Excl. Corpus Terms) | 15 | 0.1600 | 0.3056 | 0.2341 | 0.3412 |
| BM25 | Dev (English) | 7 | 0.2286 | 0.5000 | 0.3529 | 0.5337 |
| BM25 | Dev (Hinglish) | 4 | 0.2500 | 0.3542 | 0.3540 | 0.5270 |
| BM25 | Dev (Hindi - Zero Tokens) | 6 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| BM25 | Test (All Evaluable) | 17 | 0.1647 | 0.3039 | 0.2843 | 0.4785 |
| BM25 | Test (Excl. Corpus Terms) | 13 | 0.1385 | 0.2436 | 0.2308 | 0.3821 |
| BM25 | Test (English) | 6 | 0.2667 | 0.4167 | 0.4244 | 0.6704 |
| BM25 | Test (Hinglish) | 6 | 0.2000 | 0.4444 | 0.3813 | 0.6853 |
| BM25 | Test (Hindi - Zero Tokens) | 5 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| QL-Dirichlet | Dev (All Evaluable) | 17 | 0.1294 | 0.2549 | 0.1829 | 0.3007 |
| QL-Dirichlet | Dev (Excl. Corpus Terms) | 15 | 0.1333 | 0.2667 | 0.1813 | 0.2924 |
| QL-Dirichlet | Dev (English) | 7 | 0.2000 | 0.4167 | 0.2784 | 0.4683 |
| QL-Dirichlet | Dev (Hinglish) | 4 | 0.2000 | 0.3542 | 0.2899 | 0.4584 |
| QL-Dirichlet | Dev (Hindi - Zero Tokens) | 6 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| QL-Dirichlet | Test (All Evaluable) | 17 | 0.1765 | 0.3431 | 0.2677 | 0.4693 |
| QL-Dirichlet | Test (Excl. Corpus Terms) | 13 | 0.1385 | 0.2949 | 0.2045 | 0.3684 |
| QL-Dirichlet | Test (English) | 6 | 0.2667 | 0.4722 | 0.3635 | 0.6246 |
| QL-Dirichlet | Test (Hinglish) | 6 | 0.2333 | 0.5000 | 0.3949 | 0.7052 |
| QL-Dirichlet | Test (Hindi - Zero Tokens) | 5 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| QL-Jelinek-Mercer | Dev (All Evaluable) | 17 | 0.1294 | 0.2696 | 0.2056 | 0.3147 |
| QL-Jelinek-Mercer | Dev (Excl. Corpus Terms) | 15 | 0.1333 | 0.2833 | 0.2082 | 0.3083 |
| QL-Jelinek-Mercer | Dev (English) | 7 | 0.2000 | 0.4524 | 0.3285 | 0.5018 |
| QL-Jelinek-Mercer | Dev (Hinglish) | 4 | 0.2000 | 0.3542 | 0.2990 | 0.4594 |
| QL-Jelinek-Mercer | Dev (Hindi - Zero Tokens) | 6 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| QL-Jelinek-Mercer | Test (All Evaluable) | 17 | 0.1765 | 0.3039 | 0.2735 | 0.4762 |
| QL-Jelinek-Mercer | Test (Excl. Corpus Terms) | 13 | 0.1385 | 0.2436 | 0.2141 | 0.3782 |
| QL-Jelinek-Mercer | Test (English) | 6 | 0.2667 | 0.4167 | 0.3892 | 0.6634 |
| QL-Jelinek-Mercer | Test (Hinglish) | 6 | 0.2333 | 0.4444 | 0.3858 | 0.6860 |
| QL-Jelinek-Mercer | Test (Hindi - Zero Tokens) | 5 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

---

## System Limitations
1. **Preliminary Qrels:** Evaluation relevance judgments (`data/evaluation/complaints.json`, `data/evaluation/qrels.trec`) are research annotations marked "preliminary, qrels pending human verification".
2. **Hindi Lexical Retrieval Unsupported:** The shared analyzer utilizes an alphanumeric regex `\b[a-z0-9]+\b` which strips Devanagari script. Pure Hindi complaints produce 0 retrieval tokens (scoring 0.0 by construction) due to vocabulary mismatch. No translation has been added.
3. **OCR Noise in Misleading Advertisements:** The Misleading Ads Guidelines were extracted from an OCR scan of a printed compilation containing noisy text artifacts (e.g., `Advertisernents`, `Endorsernents`).

---

## Future Work
The following modules are explicitly designated as future work:
1. **Classification:** Automated complaint classification and multi-label legal issue categorization.
2. **Information Extraction:** Deep named-entity recognition and relation extraction for complex multi-party dispute facts.
3. **Query Expansion:** Domain-specific legal ontology and pseudo-relevance feedback expansion.

---

## Setup & Execution Commands

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Pipeline Execution
```bash
# 1. Parse raw legal documents and generate passages.jsonl
python src/s1_fixes.py

# 2. Tokenize and preprocess passages with shared analyzer
python src/preprocess.py

# 3. Build inverted index
python src/index.py

# 4. Verify corpus invariants and content assertions
python tests/test_corpus_s1.py

# 5. Run retrieval evaluation benchmark (TF-IDF, BM25, QL-Dirichlet, QL-JM)
python src/evaluate.py
```

### 3. Launching the Web UI
```bash
streamlit run app.py
```
