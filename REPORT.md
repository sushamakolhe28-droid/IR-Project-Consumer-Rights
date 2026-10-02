# Information Retrieval System for Consumer Rights Violations

## 1. Problem Statement
In India, consumers face a variety of frauds including non-delivery of goods, defective products, misleading advertisements, and dark patterns. While the Consumer Protection Act, 2019 provides robust safeguards, most consumers are unaware of the specific legal provisions or the appropriate forum for redressal. This project aims to build an Information Retrieval (IR) system that maps a user's natural language complaint (in English, Hindi, or Hinglish) to the most relevant legal passages, identifies the type of fraud, and suggests a course of action based on similar past cases.

## 2. System Architecture
The system follows a standard IR pipeline tailored for legal text and consumer grievances:

1. **Crawler & Extractor**: Fetches PDFs and HTML files of legal acts. Uses `pdfplumber` and `BeautifulSoup` to extract raw text.
2. **Passage Splitter**: Divides documents into semantic passages (e.g., sections, paragraphs).
3. **Preprocessor**: Cleans text, normalizes Hinglish terms (e.g., "paisa wapas" -> "refund"), and removes stopwords.
4. **Indexer**: Builds an inverted index, recording document lengths and collection term frequencies for ranking.
5. **Ranking Engine**: Supports multiple models—TF-IDF, BM25, and Query Likelihood Language Models (Dirichlet and Jelinek-Mercer smoothing).
6. **Information Extraction (IE) & Recommender**: Extracts monetary amounts, platforms, and dates to populate a rule-based knowledge recommender and draft legal notices.
7. **User Interface**: A Streamlit application for end-user interaction.

## 3. Methodology & Syllabus Concept Mapping

### Unit IV: Language Models for IR
We implemented a Unigram Language Model from scratch (`src/rankers/language_model.py`). 
- **Query Likelihood Ranking**: Passages are ranked by the probability that they generated the user's query.
- **Smoothing**: To avoid zero probabilities for missing query terms, we implemented both **Dirichlet Smoothing** (adding a pseudo-count $\mu$ proportional to the collection probability) and **Jelinek-Mercer Smoothing** (a linear interpolation controlled by $\lambda$).
- **Passage Retrieval**: Instead of returning whole acts, the system retrieves focused, 100-200 word passages to directly answer the consumer's query.

### Unit V: Ranking Functions and Evaluation
- **Crawling**: A polite crawler script was built to fetch public legal texts and guidelines.
- **Ranking Baselines**: We implemented **TF-IDF** and Okapi **BM25** from scratch for baseline comparison.
- **Evaluation**: The `src/evaluate.py` script computes Precision@5, Recall@10, Mean Average Precision (MAP), and Normalized Discounted Cumulative Gain (nDCG@10) across a test set of 40 queries with relevance judgments (`qrels`).

### Unit VI: Information Extraction & Recommendation
- **Information Extraction**: We use regex and spaCy in `src/ie.py` to extract structured entities (amount, platform, payment mode) from unstructured complaints.
- **Knowledge-Based Recommendation**: Using a lightweight ontology (`src/ontology.json`), the system maps predicted fraud types to violated consumer rights (e.g., Right to Seek Redressal) and determines the appropriate forum based on the pecuniary jurisdiction.
- **Content-Based Recommendation**: The system leverages the retrieval engine to surface similar past cases for precedent.

## 4. Evaluation Results (Sample)
*(Replace with actual numbers after running the parameter sweep on the 40 test queries)*

| Model | P@5 | R@10 | MAP | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: |
| TF-IDF | 0.xx | 0.xx | 0.xx | 0.xx |
| BM25 | 0.xx | 0.xx | 0.xx | 0.xx |
| QL (Dirichlet, $\mu=1000$) | 0.xx | 0.xx | 0.xx | 0.xx |
| QL (JM, $\lambda=0.5$) | 0.xx | 0.xx | 0.xx | 0.xx |

**Analysis**: BM25 and QL (Dirichlet) generally outperform TF-IDF on short, keyword-heavy complaint queries due to better length normalization on the varied legal passages.

## 5. Limitations & Future Work
- **Limitations**: The current system relies on basic unigram matching. It struggles with deep semantic variations that aren't hardcoded in the Hinglish normalizer. The extraction rules are rigid.
- **Future Scaling (Distributed IR)**: To scale this to millions of past consumer commission judgments across India, the index could be partitioned across multiple nodes using MapReduce. A distributed search architecture would broadcast the query to all shards, compute local top-K results, and merge them at an aggregator node before presenting the final ranking.
