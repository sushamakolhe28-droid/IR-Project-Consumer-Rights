import re

def parse_monetary_amount(text):
    """
    Extracts monetary consideration amounts from legal text or complaint descriptions.
    Rules:
    - Only treat a number as an amount if preceded or followed by a currency marker
      (Rs, Rs., INR, rupees, or the rupee symbol ₹), OR followed by lakh or crore (also 'lac').
    - Never treat 4-digit years (1900-2100) or numbers inside dates as amounts.
    """
    if not text:
        return []

    # 1. Mask dates and standalone 4-digit years (1900-2100) so numbers inside dates
    # or years are never parsed as monetary amounts.
    date_patterns = [
        # Full textual dates: e.g. September 20, 2026; 20th September 2026; Sept 20 2026; 20-Sep-2026
        r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:\s*,\s*|\s+)(?:19\d\d|20\d\d|2100)\b',
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\.?(?:\s*,\s*|\s+)(?:19\d\d|20\d\d|2100)\b',
        r'\b\d{1,2}(?:st|nd|rd|th)?[-/](?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[-/](?:19\d\d|20\d\d|2100|\d{2})\b',
        # Partial textual dates: e.g. September 20; 20th September
        r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\.?\s+\d{1,2}(?:st|nd|rd|th)?\b',
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\.?\b',
        # Numeric dates: e.g. 20/09/2026, 20-09-2026, 20.09.2026, 2026-09-20
        r'\b\d{1,2}[/.-]\d{1,2}[/.-](?:19\d\d|20\d\d|2100|\d{2})\b',
        r'\b(?:19\d\d|20\d\d|2100)[/.-]\d{1,2}[/.-]\d{1,2}\b',
        # Year expressions: e.g. year 2026, in 2026, dated 2024
        r'\b(?:in|year|yr|dated?|during|since|of|fy|q[1-4])\s+(?:19\d\d|20\d\d|2100)\b',
        # Standalone 4-digit years (1900-2100)
        r'\b(19\d\d|20\d\d|2100)\b'
    ]

    masked_chars = list(text)
    for dp in date_patterns:
        for m in re.finditer(dp, text, re.IGNORECASE):
            start, end = m.span()
            for i in range(start, end):
                masked_chars[i] = ' '
    masked_text = ''.join(masked_chars)

    curr = r'(?:rs\.?|inr|₹|rupees?)'
    unit = r'(?:crore|crores|cr|lakh|lakhs|lac|lacs)'

    patterns = [
        # 1. Preceded by currency marker: e.g. Rs 1.5 crore, Rs 45,000, ₹500, INR 1000
        rf'(?P<curr1>{curr})\s*(?P<num1>\d+(?:,\d+)*(?:\.\d+)?)\s*(?P<unit1>{unit}|thousand|k)?\b',
        # 2. Followed by unit (lakh/crore/lac): e.g. 3 crore flat, 1.5 crore, 50 lakh, 10 lac
        rf'(?:{curr}\s*)?(?P<num2>\d+(?:,\d+)*(?:\.\d+)?)\s*(?P<unit2>{unit})\b',
        # 3. Followed by currency marker: e.g. 45,000 rupees, 500 rs.
        rf'\b(?P<num3>\d+(?:,\d+)*(?:\.\d+)?)\s*(?P<unit3>{unit}|thousand|k)?\s*(?P<curr3>{curr})(?!\w)'
    ]

    amounts = []
    seen_spans = set()
    for pat in patterns:
        for m in re.finditer(pat, masked_text, re.IGNORECASE):
            if any(s < m.end() and m.start() < e for s, e in seen_spans):
                continue
            seen_spans.add((m.start(), m.end()))

            gd = m.groupdict()
            num_str = (gd.get('num1') or gd.get('num2') or gd.get('num3') or '').replace(',', '')
            unit_str = (gd.get('unit1') or gd.get('unit2') or gd.get('unit3') or '').lower()

            try:
                val = float(num_str)
                # Never treat 4-digit years (1900-2100) as amounts if unit is absent
                if not unit_str and 1900 <= val <= 2100 and val.is_integer():
                    continue

                if unit_str in ['crore', 'crores', 'cr']:
                    val *= 10000000
                elif unit_str in ['lakh', 'lakhs', 'lac', 'lacs']:
                    val *= 100000
                elif unit_str in ['thousand', 'k']:
                    val *= 1000

                raw_match = text[m.start():m.end()].strip()
                amounts.append((val, raw_match))
            except ValueError:
                pass

    return amounts


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
    
    If no valid amount is found, show_forum_box is False and only limitation
    guidance is provided.
    """
    limitation_source = "Consumer Protection Act 2019 | Section 69 Limitation period"
    limitation_note = "Two years from the date on which the cause of action has arisen."

    amounts = parse_monetary_amount(query_text)
    if not amounts:
        return {
            "show_forum_box": False,
            "amount": None,
            "raw_match": None,
            "forum_tier": None,
            "forum_name": None,
            "rule_source": None,
            "threshold_note": None,
            "limitation_source": limitation_source,
            "limitation_note": limitation_note,
        }

    max_val, raw_match = max(amounts, key=lambda x: x[0])
    forum_tier, forum_name, rule_source, threshold_note = determine_forum(max_val)

    return {
        "show_forum_box": True,
        "amount": max_val,
        "raw_match": raw_match,
        "forum_tier": forum_tier,
        "forum_name": forum_name,
        "rule_source": rule_source,
        "threshold_note": threshold_note,
        "limitation_source": limitation_source,
        "limitation_note": limitation_note,
    }
