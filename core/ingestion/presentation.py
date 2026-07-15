import fitz  # PyMuPDF
import os
from pathlib import Path
from typing import List, Dict, Any
import google.generativeai as genai

def parse_presentation_deck(file_path: Path, use_vision: bool = True, max_pages: int = -1) -> List[Dict[str, Any]]:
    """
    Parses an investor presentation slide deck (PDF format).
    For each slide:
      - Renders the slide as a compressed JPEG image.
      - Uses Gemini Vision to describe the slide's visual and textual content in parallel threads.
      - Falls back to PyMuPDF raw text extraction if Vision is unavailable or disabled.
    """
    import concurrent.futures
    doc = fitz.open(file_path)
    
    try:
        # Check if Gemini is configured and active
        from config import is_gemini_api_active
        is_gemini_active = is_gemini_api_active()

        def process_slide(page_num: int, page) -> Dict[str, Any]:
            # Deduplicate consecutive/duplicate slide layout text lines (M8)
            raw_lines = [l.strip() for l in page.get_text("text").split("\n")]
            unique_lines = []
            for line in raw_lines:
                if line and (not unique_lines or line != unique_lines[-1]):
                    unique_lines.append(line)
            slide_text = "\n".join(unique_lines).strip()
            # Render slide at 100 DPI and compress as JPEG to reduce transfer payload by 90% (M8)
            pix = page.get_pixmap(dpi=100)
            img_bytes = pix.tobytes("jpg")
            
            vision_description = ""
            analysis_type = "Raw Text"
            
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
                    
                    image_part = {
                        "mime_type": "image/jpeg",
                        "data": img_bytes
                    }
                    
                    response = model.generate_content([prompt, image_part])
                    vision_description = response.text
                    analysis_type = "Multimodal Vision Analysis"
                except Exception as e:
                    vision_description = f"[Vision analysis failed: {str(e)}]"
            
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
                
            return {
                "text": full_content,
                "metadata": {
                    "page": page_num,
                    "source": file_path.name,
                    "type": "Slide Deck",
                    "analysis_type": analysis_type
                }
            }

        num_pages = len(doc)
        if max_pages > 0:
            num_pages = min(num_pages, max_pages)

        chunks = []
        # Concurrently process slides in parallel threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(num_pages, 1)) as executor:
            futures = {executor.submit(process_slide, idx + 1, doc[idx]): idx for idx in range(num_pages)}
            for future in concurrent.futures.as_completed(futures):
                chunks.append(future.result())
                
        # Sort chunks by page number since threads return out of order
        chunks.sort(key=lambda x: x["metadata"]["page"])
        return chunks
    finally:
        doc.close()
