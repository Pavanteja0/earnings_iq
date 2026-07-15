import time
import os
from pathlib import Path
from typing import Dict, Any
import google.generativeai as genai
import fitz  # PyMuPDF fallback for transcript PDF

def analyze_call_audio(file_path: Path) -> Dict[str, Any]:
    """
    Ingests and analyzes quarterly earnings call materials.
    Supports:
      - Audio files (.mp3, .wav): Uploads to Gemini File API for multimodal audio analysis.
      - Text transcript files (.txt, .pdf): Extracts text directly for qualitative analysis.
    
    Returns a dictionary with:
      - transcript: The full transcript text or detailed summary.
      - analysis: Sentiment, management tone, and Q&A friction analysis.
      - metadata: Source details.
    """
    suffix = file_path.suffix.lower()
    
    # Check if Gemini is configured and active
    from config import is_gemini_api_active
    is_gemini_active = is_gemini_api_active()

    # Handle Text Transcript Fallback (PDF or TXT)
    if suffix in [".txt", ".pdf"]:
        transcript_text = ""
        if suffix == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                transcript_text = f.read()
        else:  # PDF
            doc = fitz.open(file_path)
            try:
                pages_text = []
                for page in doc:
                    pages_text.append(page.get_text("text"))
                transcript_text = "\n".join(pages_text)
            finally:
                doc.close()
            
        # Analyze the text transcript using Gemini (if active) or a rule-based mock
        analysis_text = ""
        if is_gemini_active:
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = (
                    "You are an expert equity research analyst. Analyze this earnings call transcript text. "
                    "Extract the following qualitative details:\n"
                    "1. Executive Tone: Is management confident, defensive, or cautious? Quote examples.\n"
                    "2. Analyst Q&A Dynamics: List the top 3 most challenging questions asked by analysts, "
                    "how management responded, and if there was any hesitation or evasion.\n"
                    "3. Key Strategic Takeaways: What are the main product, market, or guidance updates?\n"
                    "Provide a structured analysis."
                )
                response = model.generate_content([prompt, transcript_text[:100000]])  # Limit token size safely
                analysis_text = response.text
            except Exception as e:
                analysis_text = f"[Text analysis failed: {str(e)}]"
        else:
            analysis_text = (
                "### Ingestion Mode: Text Transcript (Offline/Mock Mode)\n"
                "Management expressed a cautious yet optimistic tone. Analysts pushed hard on operating margins and "
                "supply chain concerns, with management reassuring that cost optimization initiatives are on track."
            )
            
        return {
            "transcript": transcript_text,
            "analysis": analysis_text,
            "metadata": {
                "source": file_path.name,
                "type": "Transcript File",
                "mode": "text"
            }
        }
        
    # Handle Real Audio File Ingestion (.mp3, .wav, etc.)
    elif suffix in [".mp3", ".wav", ".m4a"]:
        if not is_gemini_active:
            # Fallback mock analysis when API key is missing
            return {
                "transcript": "Audio transcription is only available when a valid GEMINI_API_KEY is configured.",
                "analysis": (
                    "### Ingestion Mode: Audio (Offline Mock Mode)\n"
                    "API key missing. The audio was ingested but couldn't be sent to the Gemini File API. "
                    "Provide a GEMINI_API_KEY to trigger native multimodal audio transcription and tone analysis."
                ),
                "metadata": {
                    "source": file_path.name,
                    "type": "Audio Call File",
                    "mode": "mock"
                }
            }
            
        audio_file = None
        try:
            # Upload the audio file to the Gemini File API
            print(f"Uploading audio file {file_path} to Gemini File API...")
            audio_file = genai.upload_file(path=str(file_path))
            print(f"File uploaded. Current state: {audio_file.state.name}")
            
            # Wait for file processing to complete (state polling with safety timeout)
            retries = 36  # Wait at most 3 minutes (36 * 5s)
            while retries > 0:
                state_name = getattr(audio_file.state, "name", str(audio_file.state)).upper()
                if state_name != "PROCESSING":
                    break
                print(f"Waiting for audio processing to finish... ({retries*5}s remaining)")
                time.sleep(5)
                audio_file = genai.get_file(audio_file.name)
                retries -= 1
                
            state_name = getattr(audio_file.state, "name", str(audio_file.state)).upper()
            if state_name == "FAILED":
                raise Exception("Gemini File API processing failed.")
                
            print("Audio processing complete. Querying Gemini for transcription and qualitative tone analysis...")
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = (
                "You are an expert equity research analyst. Listen to this earnings call audio carefully. "
                "1. Transcribe the main call or provide a detailed, timestamp-grounded transcript summary "
                "of the management remarks and the analyst Q&A.\n"
                "2. Conduct a qualitative sentiment audit:\n"
                "   - Assess management's vocal cues: note any long pauses, defensive pacing, changes in tone, "
                "     or hesitation (especially during the Q&A session).\n"
                "   - Note analyst friction: where did analysts push back, and where did management sound most hesitant?\n"
                "   - Extract the core strategic/guidance figures discussed.\n"
                "Provide a highly detailed report with timestamp references."
            )
            
            response = model.generate_content([prompt, audio_file])
            
            return {
                "transcript": response.text,
                "analysis": response.text,
                "metadata": {
                    "source": file_path.name,
                    "type": "Audio Call File",
                    "mode": "audio_multimodal"
                }
            }
            
        except Exception as e:
            return {
                "transcript": f"Audio processing error: {str(e)}",
                "analysis": f"Could not perform audio analysis due to an error: {str(e)}",
                "metadata": {
                    "source": file_path.name,
                    "type": "Audio Call File",
                    "mode": "error"
                }
            }
        finally:
            # Guarantee garbage collection from Gemini Cloud File API
            if audio_file is not None:
                try:
                    genai.delete_file(audio_file.name)
                    print(f"Successfully deleted temp audio file {audio_file.name} from Gemini File API.")
                except Exception as de:
                    print(f"Failed to clean up temp audio file {audio_file.name}: {de}")
            
    else:
        raise ValueError(f"Unsupported file format: {suffix}")
