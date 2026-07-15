import fitz  # PyMuPDF
import re
from pathlib import Path
from typing import List, Dict, Any

def parse_10q_pdf(file_path: Path, max_pages: int = -1) -> List[Dict[str, Any]]:
    """
    Parses a 10-Q or 10-K PDF file, extracts text, tracks report sections,
    and returns a list of text chunks with rich metadata.
    
    Metadata includes:
      - page: 1-indexed page number
      - section: identified section (e.g., 'Item 1. Financial Statements')
      - source: filename
    """
    doc = fitz.open(file_path)
    chunks = []
    
    try:
        # Common SEC filing sections
        section_patterns = [
            r"(PART\s+[I|V]+)",
            r"(ITEM\s+\d+[A-Z]?\.\s+[^.\n]+)",
            r"(Item\s+\d+[a-z]?\.\s+[^.\n]+)"
        ]
        compiled_patterns = [re.compile(p, re.IGNORECASE) for p in section_patterns]
        
        current_section = "Front Page / Table of Contents"
        
        for page_idx, page in enumerate(doc):
            if max_pages > 0 and page_idx >= max_pages:
                break
            
            text = page.get_text("text")
            
            # Try to extract the printed page number from headers/footers (M9)
            printed_page_num = None
            text_lines = [l.strip() for l in text.split("\n") if l.strip()]
            candidate_lines = text_lines[-3:] + text_lines[:3] if len(text_lines) >= 6 else text_lines
            for line in candidate_lines:
                page_match = re.search(r"^(?:page\s+)?(\d+)(?:\s+of\s+\d+)?$", line, re.IGNORECASE)
                if page_match:
                    try:
                        val = int(page_match.group(1))
                        # Printed page shouldn't be radically different from the page index
                        if abs(val - (page_idx + 1)) <= 5: 
                            printed_page_num = val
                            break
                    except ValueError:
                        pass
            
            page_num = printed_page_num if printed_page_num is not None else (page_idx + 1)
            
            # Look for section headers on this page to update current_section
            lines = text.split("\n")
            for line in lines[:10]:  # Usually headers appear in the first few lines of a page
                line_stripped = line.strip()
                for pattern in compiled_patterns:
                    match = pattern.match(line_stripped)
                    if match:
                        if len(line_stripped) < 100:
                            current_section = line_stripped
                            break
            
            # Chunk the page text. Split paragraphs/sentences and use sliding overlap.
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            
            # Collect all paragraphs and split huge ones by sentences
            max_chunk_size = 1500  # characters
            overlap_size = 200     # characters
            
            text_units = []
            for para in paragraphs:
                if len(para) > max_chunk_size:
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    text_units.extend([s.strip() for s in sentences if s.strip()])
                else:
                    text_units.append(para)
                    
            # Build chunks with sliding overlap (M12)
            i = 0
            while i < len(text_units):
                chunk_units = []
                chunk_len = 0
                
                j = i
                while j < len(text_units) and chunk_len + len(text_units[j]) <= max_chunk_size:
                    chunk_units.append(text_units[j])
                    chunk_len += len(text_units[j]) + 2
                    j += 1
                    
                if not chunk_units and j < len(text_units):
                    chunk_units.append(text_units[j])
                    j += 1
                    
                chunk_text = "\n\n".join(chunk_units)
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "page": page_num,
                        "section": current_section,
                        "source": file_path.name,
                        "type": "10-Q"
                    }
                })
                
                # Slide start index back to achieve min overlap of overlap_size chars
                next_i = j
                if j < len(text_units):
                    overlap_accum = 0
                    backtrack = j - 1
                    while backtrack >= i and overlap_accum < overlap_size:
                        overlap_accum += len(text_units[backtrack]) + 2
                        next_i = backtrack
                        backtrack -= 1
                        
                if next_i <= i:
                    i += 1
                else:
                    i = next_i
                    
        return chunks
    finally:
        doc.close()
