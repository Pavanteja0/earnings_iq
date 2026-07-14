import fitz  # PyMuPDF
import os
from pathlib import Path
from typing import List, Dict, Any
import google.generativeai as genai

def parse_presentation_deck(file_path: Path, use_vision: bool = True) -> List[Dict[str, Any]]:
    """
    Parses an investor presentation slide deck (PDF format).
    For each slide:
      - Renders the slide as a PNG image.
      - Uses Gemini Vision to describe the slide's visual and textual content.
      - Falls back to PyMuPDF raw text extraction if Vision is unavailable or disabled.
    """
    doc = fitz.open(file_path)
    chunks = []
    
    # Check if Gemini is configured and active
    from config import is_gemini_api_active
    is_gemini_active = is_gemini_api_active()

    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        slide_text = page.get_text("text").strip()
        
        # Step 1: Render slide page to image bytes for vision analysis
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        
        vision_description = ""
        analysis_type = "Raw Text"
        
        # Step 2: Use Gemini Vision to transcribe the slide's charts and details
        if use_vision and is_gemini_active:
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = (
                    "You are an expert equity research analyst. Analyze this investor presentation slide image. "
                    "1. Extract and write down all visible text, titles, subtitles, and labels. "
                    "2. Transcribe any table data or chart metrics (identify values, axes, and trends). "
                    "3. Summarize the core message and key takeaway of this slide in 2-3 sentences. "
                    "Be extremely precise with numbers. Do not summarize or approximate values; extract them exactly."
                )
                
                # Format for Gemini API
                image_part = {
                    "mime_type": "image/png",
                    "data": img_bytes
                }
                
                response = model.generate_content([prompt, image_part])
                vision_description = response.text
                analysis_type = "Multimodal Vision Analysis"
            except Exception as e:
                # Log error and fallback to raw text
                vision_description = f"[Vision analysis failed: {str(e)}]"
        
        # Combine information. If vision succeeded, combine it with raw text. Otherwise, use raw text.
        if vision_description:
            full_content = (
                f"--- SLIDE {page_num} SUMMARY ({analysis_type}) ---\n"
                f"{vision_description}\n\n"
                f"--- SLIDE {page_num} RAW TEXT ---\n"
                f"{slide_text}"
            )
        else:
            full_content = (
                f"--- SLIDE {page_num} TEXT ---\n"
                f"{slide_text if slide_text else '[Empty slide/No extractable text]'}"
            )
            
        chunks.append({
            "text": full_content,
            "metadata": {
                "page": page_num,
                "source": file_path.name,
                "type": "Slide Deck",
                "analysis_type": analysis_type
            }
        })
        
    doc.close()
    return chunks
