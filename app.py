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
from src.query_expansion import expand_query

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

def format_passage_lines(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    pattern = re.compile(r'(?<!\n)(?<=\S)[\t ]+(\((?:[a-z]|\d+|[ivx]+)\)\s+)', re.IGNORECASE)
    formatted = pattern.sub(r'\n\1', text)
    lines = [line.strip() for line in formatted.split('\n') if line.strip()]
    return lines

def detect_complaint_category(text):
    text_lower = text.lower()
    if 'washing machine' in text_lower:
        return 'goods'
    if 'builder' in text_lower or 'delayed possession' in text_lower or 'possession' in text_lower or 'flat' in text_lower:
        return 'service'
    goods_kw = ['product', 'goods', 'machine', 'device', 'phone', 'fridge', 'laptop', 'item', 'defect', 'defective', 'spinning', 'clothes', 'shoe', 'shoes', 'appliance', 'vehicle', 'car', 'bike']
    serv_kw = ['service', 'airline', 'flight', 'ticket', 'hotel', 'travel', 'broadband', 'internet', 'telecom', 'bank', 'banking', 'insurance', 'hospital', 'doctor', 'courier', 'subscription', 'delay']
    g_score = sum(1 for k in goods_kw if k in text_lower)
    s_score = sum(1 for k in serv_kw if k in text_lower)
    if g_score > s_score:
        return 'goods'
    elif s_score > g_score:
        return 'service'
    return 'unclear'

def generate_complaint_draft(query_text, guidance):
    has_amount = bool(guidance.get('raw_match') and guidance.get('amount') is not None)
    
    if has_amount:
        amount_val = guidance['raw_match']
        forum_tier = guidance.get('forum_tier')
        if forum_tier == 'State Commission':
            forum_heading = "STATE CONSUMER DISPUTES REDRESSAL COMMISSION"
            forum_location = "[district / city name, state]"
            pecuniary_text = f"The total value of goods or services paid as consideration is {amount_val}. This Hon'ble Commission has pecuniary jurisdiction under Section 34 of the Consumer Protection Act, 2019 and Rule 4 of the Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021 (consideration exceeds fifty lakh rupees but does not exceed two crore rupees)."
        elif forum_tier == 'National Commission':
            forum_heading = "NATIONAL CONSUMER DISPUTES REDRESSAL COMMISSION"
            forum_location = "NEW DELHI"
            pecuniary_text = f"The total value of goods or services paid as consideration is {amount_val}. This Hon'ble Commission has pecuniary jurisdiction under Section 34 of the Consumer Protection Act, 2019 and Rule 5 of the Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021 (consideration exceeds two crore rupees)."
        else:
            forum_heading = "DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION"
            forum_location = "[district / city name, state]"
            pecuniary_text = f"The total value of goods or services paid as consideration is {amount_val}. This Hon'ble Commission has pecuniary jurisdiction under Section 34 of the Consumer Protection Act, 2019 and Rule 3 of the Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021 (consideration does not exceed fifty lakh rupees)."
        refund_line = f"To refund the price paid, with interest [Section 39(1)(c)] ({amount_val});"
    else:
        forum_heading = "DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION"
        forum_location = "[district / city name, state]"
        pecuniary_text = "The total value of goods or services paid as consideration is [amount paid]. Pecuniary jurisdiction is governed by Section 34 of the Consumer Protection Act, 2019 and Rules 3-5 of the Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021 (Rule 3 for consideration up to fifty lakh rupees; Rule 4 for consideration between fifty lakh and two crore rupees; Rule 5 for consideration exceeding two crore rupees)."
        refund_line = "To refund the price paid, with interest [Section 39(1)(c)];"

    defect_cues = ["defect", "defective", "faulty", "broken", "not working", "damaged", "stopped", "poor quality"]
    text_lower = query_text.lower()
    has_defect_cue = any(cue in text_lower for cue in defect_cues)

    category = detect_complaint_category(query_text)
    if category == 'goods':
        prayer_a = "To remove the defect from the goods [Section 39(1)(a)];"
    elif category == 'service':
        prayer_a = "To remove the deficiency in the service [Section 39(1)(a)];"
    else:
        prayer_a = "To remove the defect from the goods / deficiency in the service [Section 39(1)(a)];"

    if has_defect_cue:
        reliefs_block = f"""(a) {prayer_a}
(b) To replace the goods with new goods free from defects [Section 39(1)(b)];
(c) {refund_line}
(d) To pay compensation for loss, injury, or hardship suffered [Section 39(1)(d)]."""
    else:
        reliefs_block = f"""(a) {refund_line}
(b) To pay compensation for loss, injury, or hardship suffered [Section 39(1)(d)]."""

    return f"""Template draft, not legal advice.

BEFORE THE HON'BLE {forum_heading}
AT {forum_location}

CONSUMER COMPLAINT NO. ______ OF 2026
(Filed under Section 35 of the Consumer Protection Act, 2019)

IN THE MATTER OF:

[complainant name]
Address: [complainant address]
Phone: [contact number] | Email: [email]
                                                    ... COMPLAINANT

VERSUS

[seller name]
Address: [seller address]
                                                    ... OPPOSITE PARTY

MEMORANDUM OF COMPLAINT UNDER SECTION 35 OF THE CONSUMER PROTECTION ACT, 2019

The Complainant respectfully states:

1. PARTIES:
The Complainant is filing this complaint against the Opposite Party [seller name] under Section 35 of the Consumer Protection Act, 2019 in relation to goods sold/delivered or services provided/agreed to be provided.

2. STATEMENT OF FACTS & GRIEVANCE:
{query_text.strip()}

3. PECUNIARY JURISDICTION:
{pecuniary_text}

4. TERRITORIAL JURISDICTION:
This Hon'ble Commission has territorial jurisdiction under Section 34 of the Consumer Protection Act, 2019 as the Complainant resides or personally works for gain, or the cause of action wholly or in part arose, within the local limits of this Hon'ble Commission.

5. LIMITATION PERIOD:
The cause of action arose on [date]. This complaint is being filed within two years of that date, as required by Section 69 of the Consumer Protection Act, 2019. [Confirm before filing]

6. RELIEFS SOUGHT:
Under Section 39 of the Consumer Protection Act, 2019, the Complainant respectfully prays for the following reliefs:
{reliefs_block}

PLACE: [district / city name, state]
DATE: [date]

                                                    ___________________________
                                                    (SIGNATURE OF COMPLAINANT)
                                                    [complainant name]

VERIFICATION:
I, [complainant name], verify that the contents of this complaint are true to my knowledge and belief.
Verified at [district / city name, state] on [date].

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
if "has_searched" not in st.session_state:
    st.session_state["has_searched"] = False

def set_example_complaint(text):
    st.session_state["complaint_input"] = text
    st.session_state["has_searched"] = True

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

# Process search state
if search_clicked:
    if query_text.strip():
        st.session_state["has_searched"] = True
    else:
        st.session_state["has_searched"] = False

if not query_text.strip():
    st.session_state["has_searched"] = False

if search_clicked and not query_text.strip():
    st.info("👋 Please describe your problem above or click one of the examples to see your rights.")
elif st.session_state["has_searched"] and query_text.strip():
    with st.spinner("Finding relevant consumer rights and legal provisions..."):
        # 1. Retrieval
        model = models_dict[selected_model]
        user_tokens = preprocess(query_text)
        query_tokens = expand_query(query_text, user_tokens=user_tokens)
        
        if not query_tokens:
            scored_results = []
        else:
            scored = model.score(query_tokens)
            scored_results = [s for s in scored if s[1] > 0]
            
        top_5 = scored_results[:5]

        if not top_5:
            st.info("We could not find a consumer law that matches this. Describe what you bought or the service you used, what went wrong, and how much you paid.")
        else:
            # 2. Guidance Resolution
            guidance = get_forum_guidance(query_text)
            
            # 3a. Row of 3 Equal Cards
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            col_file, col_deadline, col_relief = st.columns(3)
            
            # Card 1: Where to file
            with col_file:
                if guidance["show_forum_box"]:
                    raw_amt = guidance.get('raw_match')
                    if raw_amt:
                        raw_clean = raw_amt.strip()
                        if not re.match(r'^(?:rs\.?|inr|₹)', raw_clean, re.I):
                            amt_display = f"Rs {raw_clean}"
                        else:
                            amt_display = re.sub(r'^(?:₹|inr\s*|rs\.?\s*)', 'Rs ', raw_clean, flags=re.I)
                    else:
                        amt_display = f"Rs {guidance['amount']:,.0f}" if guidance.get('amount') else ""

                    all_found = guidance.get('all_matches', [])
                    ambiguous_html = ""
                    if guidance.get('is_ambiguous') and len(all_found) > 1:
                        clean_all = []
                        for a in all_found:
                            ac = a.strip()
                            if not re.match(r'^(?:rs\.?|inr|₹)', ac, re.I):
                                clean_all.append(f"Rs {ac}")
                            else:
                                clean_all.append(re.sub(r'^(?:₹|inr\s*|rs\.?\s*)', 'Rs ', ac, flags=re.I))
                        ambiguous_html = f"""
                        <div style="font-size: 13px; color: #475569; margin-top: 4px;">All amounts found: {', '.join(clean_all)}</div>
                        <div style="color: #b45309; font-weight: 600; font-size: 13px; margin-top: 4px;">⚠️ Check the amount</div>
                        """

                    where_html = f"""
                    <div class="result-card">
                        <div>
                            <div class="card-heading">🏛️ Where to file</div>
                            <div class="card-body">
                                <div class="card-highlight"><b>{guidance['forum_name']}</b></div>
                                <div>Amount detected: <b>{amt_display}</b></div>
                                {ambiguous_html}
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

            # Official Portals to File or Register Grievance
            st.markdown(
                """<div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px 18px; margin-top: 14px; margin-bottom: 14px; font-size: 14px; color: #334155;">
                    <b>Official Portals to File or Register Grievance:</b><br/>
                    • <b>e-Daakhil Portal:</b> File your complaint electronically before District, State, or National Consumer Commissions at <a href="https://edaakhil.nic.in" target="_blank" rel="noopener noreferrer" style="color: #1d4ed8; text-decoration: underline; font-weight: 600;">edaakhil.nic.in</a> (under Section 35 of CPA 2019).<br/>
                    • <b>National Consumer Helpline (NCH):</b> Register consumer grievances for pre-litigation departmental mediation at <a href="https://consumerhelpline.gov.in" target="_blank" rel="noopener noreferrer" style="color: #1d4ed8; text-decoration: underline; font-weight: 600;">consumerhelpline.gov.in</a> or call Toll-Free <b>1915</b>.
                </div>""",
                unsafe_allow_html=True
            )

            col_portal1, col_portal2 = st.columns(2)
            with col_portal1:
                st.link_button("🌐 File Online on e-Daakhil (edaakhil.nic.in)", "https://edaakhil.nic.in", use_container_width=True)
            with col_portal2:
                st.link_button("📞 National Consumer Helpline (consumerhelpline.gov.in)", "https://consumerhelpline.gov.in", use_container_width=True)

            # Expander: only rendered when passages are found
            with st.expander("📝 Generate Ready-to-File Complaint Draft (Copy & Submit)", expanded=False):
                st.caption("A structured formal complaint draft based on Section 35 of the Consumer Protection Act, 2019. You can copy, fill in your personal details, and file directly with the Consumer Commission or on e-Daakhil.")
                st.info("Review and fill every [blank], and edit the facts (dates, what you did, what the seller said) before filing.")
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
            st.markdown("### Laws that apply to your problem")
            for rank, (doc_id, _) in enumerate(top_5, 1):
                passage_data = passages_dict.get(doc_id, {})
                raw_text = passage_data.get('text', '')
                breadcrumb = passage_data.get('metadata', {}).get('breadcrumb', doc_id)
                doc_tag = passage_data.get('metadata', {}).get('doc', '')
                
                lines = format_passage_lines(raw_text)
                
                # Top 5 passages as expanders, first expanded by default, titled with breadcrumb
                with st.expander(f"{breadcrumb}", expanded=(rank == 1)):
                    if len(lines) > 12:
                        first_8_text = "\n".join(lines[:8])
                        highlighted_first_8 = highlight_terms(first_8_text, query_text)
                        st.markdown(f'<div class="passage-text">{highlighted_first_8}</div>', unsafe_allow_html=True)
                        
                        rest_text = "\n".join(lines[8:])
                        highlighted_rest = highlight_terms(rest_text, query_text)
                        with st.expander("Show full text", expanded=False):
                            st.markdown(f'<div class="passage-text">{highlighted_rest}</div>', unsafe_allow_html=True)
                    else:
                        full_text = "\n".join(lines)
                        highlighted_body = highlight_terms(full_text, query_text)
                        st.markdown(f'<div class="passage-text">{highlighted_body}</div>', unsafe_allow_html=True)

                    st.markdown(f'<div class="passage-caption">Passage ID: {doc_id} &nbsp;|&nbsp; Document: {doc_tag}</div>', unsafe_allow_html=True)

# 3c. Footer Line
st.markdown("""
<div class="footer-container">
    <div>Information from the retrieved legal text, not legal advice.</div>
    <div class="footer-sources">Sources: Consumer Protection Act 2019, Consumer Protection (E-Commerce) Rules 2020, Guidelines for Prevention and Regulation of Dark Patterns 2023, Consumer Protection (Jurisdiction Rules) 2021, Guidelines for Prevention of Misleading Advertisements 2022.</div>
</div>
""", unsafe_allow_html=True)
