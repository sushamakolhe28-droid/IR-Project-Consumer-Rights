import re
import os
import csv

def log_correction(base_dir, filename, before, after, reason):
    csv_path = os.path.join(base_dir, 'data', 'processed', 'corrections.csv')
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['filename', 'before', 'after', 'reason'])
        writer.writerow([filename, before, after, reason])

def clean_pdf_text(pages_text, filename):
    cleaned_pages = []
    metadata_footnotes = {}
    
    is_act = "A2019" in filename
    is_jurisdiction = "Jurisdiction" in filename
    is_ecommerce = "E commerce rules" in filename
    is_dark_patterns = "Dark Patterns" in filename
    is_misleading = "Misleading" in filename
    
    is_gazette = is_jurisdiction or is_ecommerce or is_dark_patterns
    
    started_act = False
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) # roughly
    
    if is_misleading:
        metadata_footnotes['ocr_quality'] = 'noisy'
        metadata_footnotes['extraction_method'] = 'OCR'
    else:
        metadata_footnotes['extraction_method'] = 'digital'
        
    for page_num, text in enumerate(pages_text, start=1):
        if is_gazette:
            # Discard Hindi lines by checking for Devanagari characters
            lines = text.split('\n')
            english_lines = []
            for line in lines:
                if len(re.findall(r'[\u0900-\u097F]', line)) == 0:
                    # Strip gazette headers and footers
                    if "THE GAZETTE OF INDIA" in line or "EXTRAORDINARY" in line or "PART II" in line:
                        continue
                    if "Uploaded by Dte. of Printing" in line or "Published by the Controller of Publications" in line:
                        continue
                    if re.match(r'^\[F\. No\.|^\[फा\.सं\.', line) or re.match(r'^\d+$', line.strip()):
                        continue
                    english_lines.append(line)
            text = "\n".join(english_lines)
            if not text.strip():
                continue
                
        # Strip IndiaCode watermark
        text = re.sub(r'IndiaCode\d*', '', text, flags=re.IGNORECASE)
        
        if is_act:
            if "CHAPTER I" in text and "PRELIMINARY" in text:
                started_act = True
            if "STATEMENT OF OBJECTS AND REASONS" in text:
                text = text.split("STATEMENT OF OBJECTS AND REASONS")[0]
                started_act = False
            if not started_act:
                continue
                
        if is_misleading:
            # Strip book running headers (e.g., repeating document title or page numbers)
            lines = text.split('\n')
            new_lines = []
            for line in lines:
                if "Guidelines for Prevention" in line or re.match(r'^\d+$', line.strip()):
                    continue
                new_lines.append(line)
            text = "\n".join(new_lines)
            
            # OCR Corrections
            def apply_correction(t, old, new, reason):
                if old in t:
                    log_correction(base_dir, filename, old, new, reason)
                    return t.replace(old, new)
                return t
                
            text = apply_correction(text, "construer", "consumer", "OCR typo: construer -> consumer")
            text = apply_correction(text, "Section IS", "Section 18", "OCR typo: Section IS -> Section 18")
            
            # Flag cut-off end of Section 5(d)
            if "Section 5" in text or "5." in text:
                # We won't attempt to reconstruct, but we can tag it if we see a broken sentence
                pass
                
        # Move footnotes to metadata
        lines = text.split('\n')
        main_lines = []
        in_footnote = False
        page_footnotes = []
        
        for i, line in enumerate(lines):
            if (i > len(lines) - 10 and re.match(r'^\d+\.\s', line)) or in_footnote:
                in_footnote = True
                page_footnotes.append(line)
            else:
                main_lines.append(line)
                
        if page_footnotes:
            metadata_footnotes[f"page_{page_num}"] = "\n".join(page_footnotes)
            
        cleaned_pages.append("\n".join(main_lines))
        
    return "\n\n".join(cleaned_pages), metadata_footnotes
