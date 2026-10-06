import re

PRICE_CUES = ['paid', 'pay', 'price', 'bought', 'buy', 'cost', 'worth', 'refund', 'consideration']
ANCILLARY_CUES = ['delivery', 'shipping', 'courier', 'installation', 'freight', 'tip', 'postage']

def _mask_dates(text):
    """
    Masks dates and standalone 4-digit years (1900-2100) with spaces so numbers inside dates
    or years are never parsed as monetary amounts.
    Preserves numbers if explicitly accompanied by currency markers or units (e.g. 'Rs 2000 crore').
    """
    if not text:
        return ""

    date_patterns = [
        r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:\s*,\s*|\s+)(?:19\d\d|20\d\d|2100)\b',
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\.?(?:\s*,\s*|\s+)(?:19\d\d|20\d\d|2100)\b',
        r'\b\d{1,2}(?:st|nd|rd|th)?[-/](?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[-/](?:19\d\d|20\d\d|2100|\d{2})\b',
        r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\.?\s+\d{1,2}(?:st|nd|rd|th)?\b',
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\.?\b',
        r'\b\d{1,2}[/.-]\d{1,2}[/.-](?:19\d\d|20\d\d|2100|\d{2})\b',
        r'\b(?:19\d\d|20\d\d|2100)[/.-]\d{1,2}[/.-]\d{1,2}\b',
        r'\b(?:in|year|yr|dated?|during|since|of|fy|q[1-4])\s+(?:19\d\d|20\d\d|2100)\b'
    ]

    masked_chars = list(text)
    for dp in date_patterns:
        for m in re.finditer(dp, text, re.IGNORECASE):
            for i in range(m.start(), m.end()):
                masked_chars[i] = ' '

    # Standalone 4-digit years (1900-2100), but not when accompanied by currency or units
    for m in re.finditer(r'\b(19\d\d|20\d\d|2100)\b', text):
        pre = text[max(0, m.start()-10):m.start()].lower()
        post = text[m.end():min(len(text), m.end()+15)].lower()
        if re.search(r'(?:rs\.?|inr|₹)\s*$', pre):
            continue
        if re.match(r'^\s*(?:crore|cr|lakh|lac|thousand|k|rs\.?|inr|₹|rupees?)', post):
            continue
        for i in range(m.start(), m.end()):
            masked_chars[i] = ' '

    return ''.join(masked_chars)


def _parse_monetary_amount_detailed(text):
    """
    Internal parser returning list of dicts with val, raw_match, span.
    Strictly parses valid Indian grouping and Western grouping, never concatenating
    separate numbers.
    """
    if not text:
        return []

    masked_text = _mask_dates(text)

    curr = r'(?:rs\.?|inr|₹|rupees?)'
    unit = r'(?:crore|crores|cr|lakh|lakhs|lac|lacs|thousand|k)'
    
    # 1. Indian grouping: \d{1,2}(?:,\d{2})+,\d{3}  (e.g., 1,00,656; 1,50,00,000)
    # 2. Western grouping: \d{1,3}(?:,\d{3})+       (e.g., 45,000; 100,656; 15,000,000)
    # 3. Plain digits:     \d+(?:\.\d+)?            (e.g., 45000, 1.5)
    num = r'(?:\b\d{1,2}(?:,\d{2})+,\d{3}(?:\.\d+)?\b|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|\b\d+(?:\.\d+)?\b)'

    patterns = [
        # Preceded by currency marker
        rf'(?P<curr1>{curr})\s*(?P<num1>{num})\s*(?P<unit1>{unit})?\b',
        # Followed by unit (lakh/crore/lac)
        rf'(?:{curr}\s*)?(?P<num2>{num})\s*(?P<unit2>{unit})\b',
        # Followed by currency marker
        rf'\b(?P<num3>{num})\s*(?P<unit3>{unit})?\s*(?P<curr3>{curr})(?!\w)'
    ]

    amounts = []
    seen_spans = set()
    for pat in patterns:
        for m in re.finditer(pat, masked_text, re.IGNORECASE):
            if any(s < m.end() and m.start() < e for s, e in seen_spans):
                continue
            seen_spans.add((m.start(), m.end()))

            gd = m.groupdict()
            num_str = (gd.get('num1') or gd.get('num2') or gd.get('num3') or '').replace(',', '').strip()
            unit_str = (gd.get('unit1') or gd.get('unit2') or gd.get('unit3') or '').lower()

            try:
                val = float(num_str)
                # Never treat standalone years as amounts if unit is absent
                if not unit_str and 1900 <= val <= 2100 and val.is_integer():
                    pre = text[max(0, m.start()-10):m.start()].lower()
                    if not re.search(r'(?:rs\.?|inr|₹)\s*$', pre) and not gd.get('curr1') and not gd.get('curr3'):
                        continue

                if unit_str in ['crore', 'crores', 'cr']:
                    val *= 10000000
                elif unit_str in ['lakh', 'lakhs', 'lac', 'lacs']:
                    val *= 100000
                elif unit_str in ['thousand', 'k']:
                    val *= 1000

                raw_match = text[m.start():m.end()].strip()
                amounts.append({
                    'val': val,
                    'raw_match': raw_match,
                    'span': (m.start(), m.end())
                })
            except ValueError:
                pass

    amounts.sort(key=lambda x: x['span'][0])
    return amounts


def parse_monetary_amount(text):
    """
    Extracts monetary consideration amounts from legal text or complaint descriptions.
    Returns a list of tuples: [(value, raw_match), ...]
    """
    detailed = _parse_monetary_amount_detailed(text)
    return [(d['val'], d['raw_match']) for d in detailed]


def _select_primary_amount(detailed_amounts, text):
    """
    Resolves multiple amounts:
    - Never merges or concatenates them.
    - Picks the amount closest to a price cue (paid, price, bought, cost, worth, refund, Rs/₹).
    - If still ambiguous, returns the largest paid-cue amount and marks is_ambiguous=True.
    """
    if not detailed_amounts:
        return None, False, []

    if len(detailed_amounts) == 1:
        return detailed_amounts[0], False, [detailed_amounts[0]['raw_match']]

    all_raw = [a['raw_match'] for a in detailed_amounts]
    text_lower = text.lower()

    # Find positions of price cues
    cue_positions = []
    for cue in PRICE_CUES:
        for m in re.finditer(r'\b' + re.escape(cue) + r'\b', text_lower):
            cue_positions.append((m.start(), m.end(), cue))

    scored = []
    for a in detailed_amounts:
        start, end = a['span']
        min_prec_dist = float('inf')
        has_direct_cue = False

        for c_start, c_end, cue in cue_positions:
            if c_end <= start:
                dist = start - c_end
                between = text_lower[c_end:start].strip()
                if dist < min_prec_dist:
                    min_prec_dist = dist
                if dist <= 30 and (not between or re.match(r'^(?:for|the|of|a|an|total|approx|around|about|sum|of\s+rs\.?|rs\.?|inr|₹)*$', between)):
                    has_direct_cue = True
            elif c_start >= end:
                dist = c_start - end
                if dist <= 15:
                    has_direct_cue = True

        # Check if this amount is an ancillary fee (e.g. delivery, shipping)
        post_text = text_lower[end:min(len(text), end + 30)]
        pre_text = text_lower[max(0, start - 30):start]
        is_ancillary = bool(re.search(r'\b(?:' + '|'.join(ANCILLARY_CUES) + r')\b', post_text) or
                            re.search(r'\b(?:' + '|'.join(ANCILLARY_CUES) + r')\b', pre_text))

        scored.append({
            'amount': a,
            'min_prec_dist': min_prec_dist,
            'has_direct_cue': has_direct_cue,
            'is_ancillary': is_ancillary,
            'val': a['val']
        })

    # If there are primary amounts and ancillary fees (like delivery 200), prefer primary
    non_ancillary = [s for s in scored if not s['is_ancillary']]
    pool = non_ancillary if non_ancillary else scored

    # Candidates with direct price cue (e.g. "paid Rs 45,000")
    direct_candidates = [s for s in pool if s['has_direct_cue']]

    if len(direct_candidates) == 1:
        # Unambiguous direct price cue match
        return direct_candidates[0]['amount'], False, all_raw
    elif len(direct_candidates) > 1:
        # Multiple amounts with direct price cue -> ambiguous, pick largest
        best = max(direct_candidates, key=lambda x: x['val'])
        return best['amount'], True, all_raw
    else:
        # Proximity to preceding cue
        candidates_with_dist = [s for s in pool if s['min_prec_dist'] < 80]
        if candidates_with_dist:
            best_by_dist = min(candidates_with_dist, key=lambda x: x['min_prec_dist'])
            tied = [s for s in candidates_with_dist if s['min_prec_dist'] == best_by_dist['min_prec_dist']]
            if len(tied) == 1:
                return best_by_dist['amount'], False, all_raw
            else:
                best = max(tied, key=lambda x: x['val'])
                return best['amount'], True, all_raw
        else:
            best = max(pool, key=lambda x: x['val'])
            return best['amount'], True, all_raw


def determine_forum(val):
    """
    Determines the appropriate consumer dispute redressal forum under
    Consumer Protection (Jurisdiction of the District Commission, the State Commission
    and the National Commission) Rules, 2021:
    - Rule 3: Up to Rs. 50 Lakh -> District Commission
    - Rule 4: Exceeds Rs. 50 Lakh up to Rs. 2 Crore -> State Commission
    - Rule 5: Exceeds Rs. 2 Crore -> National Commission
    """
    if val is None:
        return None, None, None, None
    if val <= 5000000:
        return (
            "District Commission",
            "District Consumer Disputes Redressal Commission (District Commission)",
            "Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021 | Rule 3",
            "Value of consideration does not exceed Rs. 50 Lakh (fifty lakh rupees)."
        )
    elif val <= 20000000:
        return (
            "State Commission",
            "State Consumer Disputes Redressal Commission (State Commission)",
            "Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021 | Rule 4",
            "Value of consideration exceeds Rs. 50 Lakh but does not exceed Rs. 2 Crore (two crore rupees)."
        )
    else:
        return (
            "National Commission",
            "National Consumer Disputes Redressal Commission (NCDRC)",
            "Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021 | Rule 5",
            "Value of consideration exceeds Rs. 2 Crore (two crore rupees)."
        )


def get_forum_guidance(query_text):
    """
    Extracts monetary consideration from query_text and computes pecuniary forum
    guidance as well as limitation period guidance from CPA 2019 Section 69.
    
    If no valid amount is found, or if amount exceeds sanity threshold (Rs 1,000 crore),
    show_forum_box is False and only limitation guidance is provided.
    """
    limitation_source = "Consumer Protection Act 2019 | Section 69 Limitation period"
    limitation_note = "Two years from the date on which the cause of action has arisen."

    detailed_amounts = _parse_monetary_amount_detailed(query_text)
    if not detailed_amounts:
        return {
            "show_forum_box": False,
            "amount": None,
            "raw_match": None,
            "forum_tier": None,
            "forum_name": None,
            "rule_source": None,
            "threshold_note": None,
            "all_matches": [],
            "is_ambiguous": False,
            "limitation_source": limitation_source,
            "limitation_note": limitation_note,
        }

    # Sanity check: filter out amounts above Rs 1,000 crore (10 billion rupees)
    valid_amounts = [a for a in detailed_amounts if a['val'] <= 10000000000]
    if not valid_amounts:
        # Parsed amount above Rs 1,000 crore treated as parse error -> show no forum
        return {
            "show_forum_box": False,
            "amount": None,
            "raw_match": None,
            "forum_tier": None,
            "forum_name": None,
            "rule_source": None,
            "threshold_note": None,
            "all_matches": [],
            "is_ambiguous": False,
            "limitation_source": limitation_source,
            "limitation_note": limitation_note,
        }

    chosen, is_ambiguous, all_matches = _select_primary_amount(valid_amounts, query_text)
    if not chosen or chosen['val'] > 10000000000:
        return {
            "show_forum_box": False,
            "amount": None,
            "raw_match": None,
            "forum_tier": None,
            "forum_name": None,
            "rule_source": None,
            "threshold_note": None,
            "all_matches": [],
            "is_ambiguous": False,
            "limitation_source": limitation_source,
            "limitation_note": limitation_note,
        }

    forum_tier, forum_name, rule_source, threshold_note = determine_forum(chosen['val'])

    return {
        "show_forum_box": True,
        "amount": chosen['val'],
        "raw_match": chosen['raw_match'],
        "forum_tier": forum_tier,
        "forum_name": forum_name,
        "rule_source": rule_source,
        "threshold_note": threshold_note,
        "all_matches": all_matches,
        "is_ambiguous": is_ambiguous,
        "limitation_source": limitation_source,
        "limitation_note": limitation_note,
    }
