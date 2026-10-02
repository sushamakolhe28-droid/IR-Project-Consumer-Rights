import os
import glob
import json
import re
import pdfplumber
from bs4 import BeautifulSoup
from src.validator import IngestionValidator

from src.corpus_cleaner import clean_pdf_text

import pypdfium2 as pdfium
import pytesseract
from PIL import Image

def extract_pdf(file_path):
    print(f"Extracting PDF: {file_path}")
    is_valid, msg = IngestionValidator.validate_pdf_file(file_path)
    if not is_valid:
        print(f"Validation Error for {file_path}: {msg}")
        return None, {}
        
    try:
        with pdfplumber.open(file_path) as pdf:
            pages_text = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
                    
            total_text_len = sum(len(t.strip()) for t in pages_text)
            
            # OCR Fallback if text is empty or very small
            if total_text_len < 100:
                print(f"Fallback to OCR for {os.path.basename(file_path)}")
                pages_text = []
                # Set tesseract path on Windows
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                
                pdf_doc = pdfium.PdfDocument(file_path)
                for i in range(len(pdf_doc)):
                    page = pdf_doc[i]
                    # Render to PIL image (300 dpi = scale 4 approximately)
                    pil_image = page.render(scale=4).to_pil()
                    text = pytesseract.image_to_string(pil_image, lang='eng')
                    pages_text.append(text)
                    
            text, meta = clean_pdf_text(pages_text, os.path.basename(file_path))
            return text, meta
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return None, {}

def extract_html(file_path):
    print(f"Extracting HTML: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
        return text, {}
    except Exception as e:
        print(f"Error reading HTML {file_path}: {e}")
        return None, {}

def extract_text_file(file_path):
    print(f"Extracting Text/Markdown: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        metadata = {}
        text = content
        
        # Check for header separated by '---'
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                header = parts[1]
                text = parts[2].strip()
                # Parse header
                for line in header.strip().split('\n'):
                    if ':' in line:
                        k, v = line.split(':', 1)
                        metadata[k.strip().lower()] = v.strip()
        elif '\n---\n' in content:
            parts = content.split('\n---\n', 1)
            header = parts[0]
            text = parts[1].strip()
            # If header looks like key-value pairs
            if all(':' in line for line in header.strip().split('\n') if line.strip()):
                for line in header.strip().split('\n'):
                    if ':' in line:
                        k, v = line.split(':', 1)
                        metadata[k.strip().lower()] = v.strip()
            else:
                text = content # False alarm
                
        return text, metadata
    except Exception as e:
        print(f"Error reading text file {file_path}: {e}")
        return None, {}

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    raw_dir = os.path.join(base_dir, 'data', 'raw')
    processed_dir = os.path.join(base_dir, 'data', 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    
    file_types = [
        ('*.pdf', extract_pdf),
        ('*.html', extract_html),
        ('*.txt', extract_text_file),
        ('*.md', extract_text_file)
    ]
    
    validation_failures = {}
    
    for pattern, extractor in file_types:
        for filepath in glob.glob(os.path.join(raw_dir, pattern)):
            filename = os.path.basename(filepath)
            text, meta = extractor(filepath)
            
            if text is not None:
                is_valid, msg = IngestionValidator.validate_extracted_text(filename, text)
                if not is_valid:
                    print(f"Text Validation Error for {filename}: {msg}")
                    validation_failures[filename] = msg
                    continue
                    
                out_path = os.path.join(processed_dir, f"{filename}.txt")
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                    
                if meta:
                    meta_path = os.path.join(processed_dir, f"{filename}.meta.json")
                    with open(meta_path, 'w', encoding='utf-8') as f:
                        json.dump(meta, f)
            else:
                validation_failures[filename] = "Extraction failed completely (returned None)"
                
    failures_path = os.path.join(processed_dir, 'validation_failures.json')
    with open(failures_path, 'w', encoding='utf-8') as f:
        json.dump(validation_failures, f, indent=4)

if __name__ == "__main__":
    main()
