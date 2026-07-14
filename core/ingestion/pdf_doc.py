import fitz  # PyMuPDF
import re
from pathlib import Path
from typing import List, Dict, Any

def parse_10q_pdf(file_path: Path) -> List[Dict[str, Any]]:
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
    
    # Common SEC filing sections
    section_patterns = [
        r"(PART\s+[I|V]+)",
        r"(ITEM\s+\d+[A-Z]?\.\s+[^.\n]+)",
        r"(Item\s+\d+[a-z]?\.\s+[^.\n]+)"
    ]
    compiled_patterns = [re.compile(p, re.IGNORECASE) for p in section_patterns]
    
    current_section = "Front Page / Table of Contents"
    
    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        text = page.get_text("text")
        
        # Look for section headers on this page to update current_section
        lines = text.split("\n")
        for line in lines[:10]:  # Usually headers appear in the first few lines of a page
            line_stripped = line.strip()
            for pattern in compiled_patterns:
                match = pattern.match(line_stripped)
                if match:
                    # Limit section header length to prevent swallowing large text blocks
                    if len(line_stripped) < 100:
                        current_section = line_stripped
                        break
        
        # Now chunk the page text. Let's do paragraph-based chunking with sliding window.
        # Clean up text a bit (remove consecutive newlines, etc.)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        current_chunk = []
        current_length = 0
        max_chunk_size = 1500  # characters
        overlap_size = 200     # characters
        
        for para in paragraphs:
            # If paragraph itself is huge, split it by sentences
            if len(para) > max_chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    if current_length + len(sentence) > max_chunk_size:
                        if current_chunk:
                            chunk_text = "\n".join(current_chunk)
                            chunks.append({
                                "text": chunk_text,
                                "metadata": {
                                    "page": page_num,
                                    "section": current_section,
                                    "source": file_path.name,
                                    "type": "10-Q"
                                }
                            })
                            # Sliding window: keep last few items for context overlap
                            # For simplicity, we just keep the last sentence/paragraph if it fits
                            if len(sentence) < max_chunk_size:
                                current_chunk = [sentence]
                                current_length = len(sentence)
                            else:
                                current_chunk = []
                                current_length = 0
                        else:
                            # Sentence itself is larger than max_chunk_size, append it directly
                            chunks.append({
                                "text": sentence,
                                "metadata": {
                                    "page": page_num,
                                    "section": current_section,
                                    "source": file_path.name,
                                    "type": "10-Q"
                                }
                            })
                    else:
                        current_chunk.append(sentence)
                        current_length += len(sentence) + 1
            else:
                if current_length + len(para) > max_chunk_size:
                    if current_chunk:
                        chunk_text = "\n".join(current_chunk)
                        chunks.append({
                            "text": chunk_text,
                            "metadata": {
                                "page": page_num,
                                "section": current_section,
                                "source": file_path.name,
                                "type": "10-Q"
                            }
                        })
                    current_chunk = [para]
                    current_length = len(para)
                else:
                    current_chunk.append(para)
                    current_length += len(para) + 2  # account for newlines
        
        # Add remaining text in buffer
        if current_chunk:
            chunk_text = "\n".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "page": page_num,
                    "section": current_section,
                    "source": file_path.name,
                    "type": "10-Q"
                }
            })
            
    doc.close()
    return chunks
