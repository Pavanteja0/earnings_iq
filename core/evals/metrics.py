from typing import List, Dict, Any
import google.generativeai as genai
import re

def evaluate_brief(
    brief: str, 
    retrieved_contexts: List[str]
) -> Dict[str, Any]:
    """
    Evaluates the quality, grounding, and correctness of the generated brief 
    using Gemini-as-a-judge.
    
    Evaluates:
      - Faithfulness (percentage of statements fully grounded in contexts)
      - Answer Relevance (how well the brief answers key investor questions)
      - Math Accuracy (verification of calculations in the brief)
    """
    from config import is_gemini_api_active
    is_gemini_active = is_gemini_api_active()

    if not is_gemini_active:
        # Do not return fake high scores. Indicate clearly that the system is offline.
        return {
            "faithfulness": -1.0,
            "answer_relevance": -1.0,
            "math_accuracy": -1.0,
            "overall_score": -1.0,
            "feedback": "Offline evaluation mode. Grounding evaluations (faithfulness, relevance, math accuracy) require an active GEMINI_API_KEY to run the LLM-as-a-judge suite."
        }

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Build prompt
        context_str = "\n---\n".join(retrieved_contexts[:10])  # limit size
        
        prompt = (
            "You are an independent LLMOps and RAG evaluator. Your job is to judge the quality of the generated Research Brief "
            "based strictly on the original source contexts provided below.\n\n"
            f"=== Source Contexts ===\n{context_str}\n\n"
            f"=== Generated Research Brief ===\n{brief}\n\n"
            "Evaluate the brief on three metrics. For each, give a score from 0.0 to 1.0 and a 1-sentence explanation:\n"
            "1. **Faithfulness**: Are the facts and figures in the brief fully supported by the source contexts? No external facts allowed.\n"
            "2. **Answer Relevance**: Does the brief capture the necessary analyst details (bull/bear, margins, segment revenues, tone)?\n"
            "3. **Math Accuracy**: Are all percentages, YoY growth rates, and margins mathematically sound based on the source numbers?\n\n"
            "Format your output in JSON with fields 'faithfulness_score', 'relevance_score', 'math_score', 'explanations' (dict), and 'feedback'."
        )
        
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Parse JSON response
        import json
        eval_data = json.loads(response.text.strip())
        
        # Determine actual math accuracy score deterministically!
        from core.utils.math_verifier import verify_math_claims
        math_verification = verify_math_claims(brief)
        m = math_verification.get("math_accuracy_score", 0.0)
        
        f = eval_data.get("faithfulness_score", 0.0)
        r = eval_data.get("relevance_score", 0.0)
        overall = (f + r + m) / 3.0
        
        explanations = eval_data.get("explanations", {})
        explanations["Math Accuracy (Deterministic)"] = math_verification.get("report", "No claims recalculated.")
        
        return {
            "faithfulness": f,
            "answer_relevance": r,
            "math_accuracy": m,
            "overall_score": overall,
            "explanations": explanations,
            "feedback": eval_data.get("feedback", "Evaluation successfully computed.")
        }
        
    except Exception as e:
        return {
            "faithfulness": -1.0,
            "answer_relevance": -1.0,
            "math_accuracy": -1.0,
            "overall_score": -1.0,
            "feedback": f"Evaluation crashed: {str(e)}."
        }
