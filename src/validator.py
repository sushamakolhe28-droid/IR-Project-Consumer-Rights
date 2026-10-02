import os

class IngestionValidator:
    """Validates raw documents before ingestion to prevent contaminated indexes."""
    
    # Required sanity keywords per known document
    SANITY_KEYWORDS = {
        "CONSUMER RIGHTS A2019-35.pdf": ["consumer protection act", "central authority", "district commission"],
        "Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021.pdf": ["jurisdiction", "rules", "pecuniary"],
        "The Guidelines for Prevention and Regulation of Dark Patterns, 2023_1732707717.pdf": ["dark pattern", "guidelines", "deceptive"],
        "Dark_Patterns_Guidelines.html": ["dark pattern", "guidelines", "deceptive"],
        "E commerce rules_1732703966.pdf": ["e-commerce", "rules", "consumer"],
        "Guidelines for Prevention of Misleading Advertisements & Endorsements for Mislaeding Advertisements, 2022.pdf": ["misleading", "advertisement", "guidelines"]
    }
    
    MIN_TEXT_LENGTH = 1000 # Minimum characters expected
    
    @classmethod
    def validate_pdf_file(cls, filepath):
        """Checks PDF magic bytes."""
        try:
            with open(filepath, 'rb') as f:
                header = f.read(4)
                if not header.startswith(b'%PDF'):
                    return False, f"Invalid magic bytes for PDF: {header}"
            return True, "Valid PDF magic bytes"
        except Exception as e:
            return False, f"Error reading file: {e}"
            
    @classmethod
    def validate_extracted_text(cls, filename, text):
        """Checks text length and document-specific sanity keywords."""
        if not text or len(text.strip()) < cls.MIN_TEXT_LENGTH:
            return False, f"Extracted text too short (length {len(text) if text else 0} < {cls.MIN_TEXT_LENGTH})"
            
        # Check sanity keywords if defined for this file
        keywords = cls.SANITY_KEYWORDS.get(filename)
        if keywords:
            text_lower = text.lower()
            if not any(kw in text_lower for kw in keywords):
                return False, f"Missing required sanity keywords for {filename}. Extracted content does not appear to match expected document."
                
        return True, "Valid text"

