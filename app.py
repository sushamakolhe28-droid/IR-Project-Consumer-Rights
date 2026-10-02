import streamlit as st
import os
import re
import json
from collections import Counter

from src.index import InvertedIndex
from src.preprocess import preprocess
from src.rankers.tfidf import TFIDFRanker
from src.rankers.bm25 import BM25Ranker
from src.rankers.language_model import LanguageModelRanker
from src.forum_guidance import parse_monetary_amount, get_forum_guidance, determine_forum

st.set_page_config(
    page_title="Consumer Rights Helper",
    page_icon="⚖️",
    layout="wide"
)

# Custom Styling (Centered, max 900px width, clean cards, readable typography)
st.markdown("""
<style>
    /* Content centering and max width */
    .block-container {
        max-width: 900px !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        margin: 0 auto !important;
    }
    
    /* Typography base */
    body, p, div, span, label {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        font-size: 15px;
    }

    /* Headings and primary accents */
    h1 {
        color: #1e3a8a !important;
        font-size: 2.1rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.2rem !important;
    }
    
    h3 {
        color: #1e3a8a !important;
        font-size: 1.35rem !important;
        font-weight: 600 !important;
        margin-top: 1.8rem !important;
        margin-bottom: 0.8rem !important;
    }

    /* Input area */
    .stTextArea textarea {
        font-size: 15px !important;
        border-radius: 8px !important;
        border: 1px solid #cbd5e1 !important;
    }
    .stTextArea textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 1px #2563eb !important;
    }

    /* Equal height action cards */
    .result-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 18px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 220px;
        height: 100%;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        margin-bottom: 12px;
    }
    
    .card-heading {
        font-weight: 700;
        font-size: 16px;
        color: #1e3a8a;
        margin-bottom: 8px;
    }
    
    .card-body {
        font-size: 15px;
        color: #334155;
        line-height: 1.5;
        flex-grow: 1;
    }
    
    .card-highlight {
        font-weight: 600;
        color: #1d4ed8;
        margin-bottom: 6px;
    }
    
    .card-subtext {
        font-size: 13px;
        color: #64748b;
        margin-top: 4px;
        line-height: 1.4;
    }
    
    .card-citation {
        font-size: 12px;
        color: #64748b;
        margin-top: 12px;
        border-top: 1px solid #edf2f7;
        padding-top: 6px;
    }

    /* Expandable passage styling */
    .passage-text {
        font-size: 15px;
        line-height: 1.65;
        color: #1e293b;
        white-space: pre-wrap;
        margin-top: 4px;
    }
    
    .passage-caption {
        font-size: 12.5px;
        color: #64748b;
        margin-top: 10px;
        padding-top: 6px;
        border-top: 1px dashed #e2e8f0;
    }

    /* Highlight badge in soft yellow */
    mark.highlight {
        background-color: #fef08a;
        color: #713f12;
        padding: 1px 4px;
        border-radius: 3px;
        font-weight: 500;
    }

    /* Footer styling */
    .footer-container {
        margin-top: 40px;
        padding-top: 16px;
        border-top: 1px solid #e2e8f0;
        text-align: center;
        font-size: 13px;
        color: #64748b;
    }
    
    .footer-sources {
        font-size: 11.5px;
        color: #94a3b8;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')
PASSAGES_FILE = os.path.join(DATA_DIR, 'passages.jsonl')
INDEX_FILE = os.path.join(DATA_DIR, 'index.pkl')
METRICS_FILE = os.path.join(BASE_DIR, 'results', 'metrics.json')

@st.cache_resource
def load_corpus_and_index():
    if not os.path.exists(PASSAGES_FILE) or not os.path.exists(INDEX_FILE):
        return None, None, None, "Legal corpus not ready (index or passages missing)"
        
    try:
        index_obj = InvertedIndex.load(INDEX_FILE)
        passages = {}
        with open(PASSAGES_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                p = json.loads(line)
                passages[p['passage_id']] = p
                
        if len(passages) < 200:
            return None, None, None, f"Legal corpus not ready (insufficient passages: {len(passages)} < 200)"
            
        models = {
            'BM25': BM25Ranker(index_obj, k1=1.5, b=0.75),
            'TF-IDF': TFIDFRanker(index_obj),
            'QL-Dirichlet': LanguageModelRanker(index_obj, smoothing='dirichlet', mu=1000),
            'QL-Jelinek-Mercer': LanguageModelRanker(index_obj, smoothing='jm', lambda_jm=0.5)
        }
        return index_obj, passages, models, "OK"
    except Exception as e:
        return None, None, None, f"Legal corpus not ready ({str(e)})"

index_obj, passages_dict, models_dict, health_status = load_corpus_and_index()

# 1. Header
st.title("Consumer Rights Helper")
st.markdown("<p style='font-size: 16px; color: #475569; margin-top: -6px; margin-bottom: 22px;'>Describe your problem. See which consumer law applies, where to file and by when.</p>", unsafe_allow_html=True)

if health_status != "OK":
    st.error(f"⚠️ {health_status}")
    st.stop()

def highlight_terms(text, query):
    tokens = preprocess(query)
    if not tokens:
        return text
    escaped_tokens = [re.escape(t) for t in set(tokens) if len(t) >= 2]
    if not escaped_tokens:
        return text
    pattern = re.compile(rf'\b({"|".join(escaped_tokens)}[a-z]*)\b', re.IGNORECASE)
    return pattern.sub(r'<mark class="highlight">\1</mark>', text)

def generate_complaint_draft(query_text, guidance):
    amount_str = f"{guidance['raw_match']} (approx. ₹{guidance['amount']:,.0f})" if guidance.get('raw_match') else "[Amount as per invoice / receipt]"
    forum_str = guidance['forum_name'] if guidance.get('forum_name') else "District Consumer Disputes Redressal Commission"
    
    return f"""BEFORE THE HON'BLE {forum_str.upper()}
AT [DISTRICT / CITY NAME, STATE]

CONSUMER COMPLAINT NO. ______ OF 2026
(Filed under Section 35 of the Consumer Protection Act, 2019)

IN THE MATTER OF:
[Complainant Full Name]
Aged about ___ years, S/o or D/o [Father's / Spouse's Name]
Permanent Address: [Complete Residential Address]
Current Address: [Current Postal Address]
Phone: [Mobile Number] | Email: [Email Address]
                                                    ... COMPLAINANT

VERSUS

[Opposite Party / Company / Seller / Service Provider / Builder Name]
Through its Managing Director / Authorized Representative
Registered Office: [Full Corporate / Business Address]
Branch Office (if any): [Branch Address]
Customer Care Email: [Email] | Phone: [Phone]
                                                    ... OPPOSITE PARTY

MEMORANDUM OF COMPLAINT UNDER SECTION 35 OF CPA, 2019

The Complainant most respectfully submits as follows:

1. CONSUMER STATUS:
The Complainant is a 'consumer' as defined under Section 2(7) of the Consumer Protection Act, 2019, having purchased goods / availed services from the Opposite Party for valuable consideration.

2. STATEMENT OF FACTS & GRIEVANCE:
{query_text.strip()}

3. VALUE OF CONSIDERATION & PECUNIARY JURISDICTION:
The total value of goods or services paid as consideration is {amount_str}. This Hon'ble Commission has the requisite pecuniary jurisdiction to entertain and adjudicate this complaint pursuant to the Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021.

4. TERRITORIAL JURISDICTION:
This Hon'ble Commission has territorial jurisdiction under Section 34(2) of the Consumer Protection Act, 2019 because:
(a) The Complainant resides / personally works for gain within the local limits of this Hon'ble Commission [Section 34(2)(d)]; and/or
(b) The cause of action wholly or in part arose within the jurisdiction of this Hon'ble Commission [Section 34(2)(c)].

5. LIMITATION PERIOD:
The cause of action arose on [Date when problem occurred / refusal took place]. This complaint is filed well within the statutory limitation period of two years prescribed under Section 69(1) of the Consumer Protection Act, 2019.

6. PRAYER / RELIEFS SOUGHT:
In view of the above facts, and as provided under Section 39(1) of the Consumer Protection Act, 2019, the Complainant respectfully prays that this Hon'ble Commission may be pleased to direct the Opposite Party:
(a) To remove the defect in the goods / deficiency in service [Section 39(1)(a)];
(b) To replace the defective product with a new product of similar description free from defects [Section 39(1)(b)];
(c) To refund the entire consideration amount of {amount_str} along with interest [Section 39(1)(c)];
(d) To pay an amount of Rs. [Amount] as compensation for mental agony, financial loss, and hardship suffered due to negligence and unfair trade practice [Section 39(1)(d)];
(e) To pay Rs. [Amount] towards litigation expenses; and
(f) Pass any other order or grant such further relief as this Hon'ble Commission may deem fit in the interest of justice.

PLACE: [City]
DATE: [Date]

                                                    ___________________________
                                                    (SIGNATURE OF COMPLAINANT)
                                                    [Complainant Full Name]

VERIFICATION:
I, the Complainant above-named, do hereby solemnly declare and verify that the facts stated in paragraphs 1 to 6 above are true and correct to my personal knowledge and belief, and nothing material has been concealed therefrom.
Verified at [City] on this [Day] of [Month], 2026.

                                                    ___________________________
                                                    (SIGNATURE OF COMPLAINANT)
"""

# Check for dev mode in query parameters: ?dev=1
is_dev_mode = False
try:
    if hasattr(st, "query_params"):
        is_dev_mode = (st.query_params.get("dev") == "1")
except Exception:
    is_dev_mode = False

if is_dev_mode:
    with st.expander("⚙️ Advanced", expanded=False):
        selected_model = st.selectbox(
            "Retrieval Model:",
            options=["BM25", "TF-IDF", "QL-Dirichlet", "QL-Jelinek-Mercer"],
            index=0
        )
        st.caption("Default model works best for most complaints.")
else:
    selected_model = "BM25"

# 2. Input Section
if "complaint_input" not in st.session_state:
    st.session_state["complaint_input"] = ""

def set_example_complaint(text):
    st.session_state["complaint_input"] = text

query_text = st.text_area(
    "Describe your consumer complaint:",
    key="complaint_input",
    placeholder="Describe your problem in your own words",
    height=110,
    label_visibility="collapsed"
)

# Primary Action Button
search_clicked = st.button("Find my rights", type="primary", use_container_width=True)

# 3 Clickable Example Complaints below the box
st.markdown("<div style='margin-top: 10px; margin-bottom: 6px; font-size: 13.5px; color: #64748b;'>Or try an example:</div>", unsafe_allow_html=True)
col_ex1, col_ex2, col_ex3 = st.columns(3)

EX_DEFECTIVE = "I bought a washing machine on September 20, 2026, but it stopped spinning after two weeks. The service center refuses to repair or replace it."
EX_REFUND = "I ordered clothes from an online store, returned them within the return window, but the seller refused to refund my money."
EX_CHARGES = "An airline ticket booking website added hidden convenience fees and pre-selected travel insurance at checkout without my consent."

with col_ex1:
    st.button("Defective product", on_click=set_example_complaint, args=(EX_DEFECTIVE,), use_container_width=True)
with col_ex2:
    st.button("Refund refused online", on_click=set_example_complaint, args=(EX_REFUND,), use_container_width=True)
with col_ex3:
    st.button("Hidden charges at checkout", on_click=set_example_complaint, args=(EX_CHARGES,), use_container_width=True)

# Process search
has_query = bool(query_text.strip())

if search_clicked and not has_query:
    st.info("👋 Please describe your problem above or click one of the examples to see your rights.")
elif has_query:
    with st.spinner("Finding relevant consumer rights and legal provisions..."):
        # 1. Guidance Resolution
        guidance = get_forum_guidance(query_text)
        
        # 3a. Row of 3 Equal Cards
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        col_file, col_deadline, col_relief = st.columns(3)
        
        # Card 1: Where to file
        with col_file:
            if guidance["show_forum_box"]:
                where_html = f"""
                <div class="result-card">
                    <div>
                        <div class="card-heading">🏛️ Where to file</div>
                        <div class="card-body">
                            <div class="card-highlight"><b>{guidance['forum_name']}</b></div>
                            <div>For consideration of <b>{guidance['raw_match']}</b> (approx. ₹{guidance['amount']:,.0f}).</div>
                            <div class="card-subtext">Other tiers: District (≤ ₹50 Lakh), State (₹50L–₹2 Crore), National (> ₹2 Crore).</div>
                            <div style="margin-top: 6px;">You can file where you live, where the problem happened, or online.</div>
                        </div>
                    </div>
                    <div class="card-citation">Jurisdiction Rules 2021 | Rules 3–5; CPA 2019 Section 34(2), 35</div>
                </div>
                """
            else:
                where_html = """
                <div class="result-card">
                    <div>
                        <div class="card-heading">🏛️ Where to file</div>
                        <div class="card-body">
                            <div>Which commission you go to depends on the amount you paid. Add the amount (for example Rs 45,000) to see yours.</div>
                            <div class="card-subtext">Tiers: District (≤ ₹50 Lakh), State (₹50L–₹2 Crore), National (> ₹2 Crore).</div>
                            <div style="margin-top: 6px;">You can file where you live, where the problem happened, or online.</div>
                        </div>
                    </div>
                    <div class="card-citation">Jurisdiction Rules 2021 | Rules 3–5; CPA 2019 Section 34(2), 35</div>
                </div>
                """
            st.markdown(where_html, unsafe_allow_html=True)

        # Card 2: Deadline
        with col_deadline:
            deadline_html = """
            <div class="result-card">
                <div>
                    <div class="card-heading">⏳ Deadline</div>
                    <div class="card-body">
                        <div>File within <b>two years</b> from the date on which the cause of action arose.</div>
                        <div style="margin-top: 6px;">Late complaints may be admitted only if you satisfy the Commission that you had sufficient cause for delay.</div>
                    </div>
                </div>
                <div class="card-citation">Consumer Protection Act 2019 | Section 69</div>
            </div>
            """
            st.markdown(deadline_html, unsafe_allow_html=True)

        # Card 3: You can ask for
        with col_relief:
            relief_html = """
            <div class="result-card">
                <div>
                    <div class="card-heading">⚖️ You can ask for</div>
                    <div class="card-body">
                        <div>• <b>Remove defect</b> or <b>replace goods</b> with new defect-free goods</div>
                        <div style="margin-top: 3px;">• <b>Full refund</b> of price or charges paid, with interest</div>
                        <div style="margin-top: 3px;">• <b>Compensation</b> for loss, injury or punitive damages</div>
                    </div>
                </div>
                <div class="card-citation">Consumer Protection Act 2019 | Section 39(1)(a)-(d)</div>
            </div>
            """
            st.markdown(relief_html, unsafe_allow_html=True)

        # Official Filing Links & Ready-to-file Complaint Draft
        st.markdown("""
        <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 18px; margin-top: 14px; margin-bottom: 14px; font-size: 14px; color: #334155;">
            <b>Official Portals to File or Register Grievance:</b><br/>
            • <b>e-Daakhil Portal:</b> File your complaint electronically before District, State, or National Consumer Commissions at <a href="https://edaakhil.nic.in" target="_blank" style="color: #1d4ed8; text-decoration: underline; font-weight: 600;">edaakhil.nic.in</a> (under Section 35 of CPA 2019).<br/>
            • <b>National Consumer Helpline (NCH):</b> Register consumer grievances for pre-litigation departmental mediation at <a href="https://consumerhelpline.gov.in" target="_blank" style="color: #1d4ed8; text-decoration: underline; font-weight: 600;">consumerhelpline.gov.in</a> or call Toll-Free <b>1915</b>.
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📝 Generate Ready-to-File Complaint Draft (Copy & Submit)", expanded=False):
            st.caption("A structured formal complaint draft based on Section 35 of the Consumer Protection Act, 2019. You can copy, fill in your personal details, and file directly with the Consumer Commission or on e-Daakhil.")
            complaint_draft = generate_complaint_draft(query_text, guidance)
            st.code(complaint_draft, language="text")
            st.download_button(
                label="📥 Download Complaint Draft (.txt)",
                data=complaint_draft,
                file_name="consumer_complaint_draft.txt",
                mime="text/plain",
                use_container_width=True
            )

        # 3b. Laws that apply to your problem
        model = models_dict[selected_model]
        query_tokens = preprocess(query_text)
        
        st.markdown("### Laws that apply to your problem")
        
        if not query_tokens:
            st.info("ℹ️ No retrieval tokens were produced for this query. If this is a Hindi query, pure Devanagari text is stripped by the retrieval analyzer (vocabulary-mismatch limitation).")
        else:
            scored_results = model.score(query_tokens)
            top_5 = scored_results[:5]
            
            if not top_5:
                st.info("No matching legal passages found in the corpus.")
            else:
                for rank, (doc_id, _) in enumerate(top_5, 1):
                    passage_data = passages_dict.get(doc_id, {})
                    raw_text = passage_data.get('text', '')
                    breadcrumb = passage_data.get('metadata', {}).get('breadcrumb', doc_id)
                    doc_tag = passage_data.get('metadata', {}).get('doc', '')
                    
                    highlighted_body = highlight_terms(raw_text, query_text)
                    
                    # Top 5 passages as expanders, first expanded by default, titled with breadcrumb
                    with st.expander(f"{breadcrumb}", expanded=(rank == 1)):
                        st.markdown(f'<div class="passage-text">{highlighted_body}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="passage-caption">Passage ID: {doc_id} &nbsp;|&nbsp; Document: {doc_tag}</div>', unsafe_allow_html=True)

# 3c. Footer Line
st.markdown("""
<div class="footer-container">
    <div>Information from the retrieved legal text, not legal advice.</div>
    <div class="footer-sources">Sources: Consumer Protection Act 2019, Consumer Protection (E-Commerce) Rules 2020, Guidelines for Prevention and Regulation of Dark Patterns 2023, Consumer Protection (Jurisdiction Rules) 2021, Guidelines for Prevention of Misleading Advertisements 2022.</div>
</div>
""", unsafe_allow_html=True)
