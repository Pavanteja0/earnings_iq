import google.generativeai as genai
from typing import List, Dict, Any, Optional

class BaseAgent:
    """
    Base class for agents in the multi-agent system.
    Tracks reasoning logs and handles communication with the LLM.
    """
    def __init__(self, name: str, role: str, system_prompt: str, model_name: Optional[str] = None):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.logs: List[Dict[str, str]] = []  # List of dicts: {"action": str, "details": str}

    def log(self, action: str, details: str):
        """Logs internal agent reasoning and operations."""
        print(f"[{self.name}] {action}: {details[:120]}...")
        self.logs.append({"action": action, "details": details})

    def run_llm(
        self, 
        user_prompt: str, 
        context: Optional[str] = None, 
        temperature: float = 0.2
    ) -> str:
        """
        Executes a call to Gemini using the agent's system prompt and provided context.
        """
        self.log("Invoking LLM", f"Prompt length: {len(user_prompt)}")
        
        # Configure model
        from config import is_gemini_api_active, DEFAULT_GEMINI_MODEL
        is_gemini_active = is_gemini_api_active()

        if not is_gemini_active:
            self.log("LLM Bypassed", "Using mock response due to missing API key")
            return self.get_mock_response(user_prompt)

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name or DEFAULT_GEMINI_MODEL,
                system_instruction=self.system_prompt
            )
            
            full_prompt = ""
            if context:
                full_prompt += f"--- CONTEXT REFERENCE ---\n{context}\n\n"
            full_prompt += f"--- USER INSTRUCTION ---\n{user_prompt}"

            # API Rate-Limit (HTTP 429) retry buffer with exponential backoff
            import time
            retries = 3
            backoff = 2
            response = None
            
            for attempt in range(retries):
                try:
                    response = model.generate_content(
                        full_prompt,
                        generation_config={"temperature": temperature}
                    )
                    break
                except Exception as ex:
                    err_str = str(ex).lower()
                    if ("429" in err_str or "resource" in err_str or "quota" in err_str or "exhausted" in err_str) and attempt < retries - 1:
                        import random
                        # M7: Add random jitter to prevent retry storms in concurrent loops
                        sleep_time = (backoff ** attempt) + random.uniform(0, 0.5)
                        self.log("Rate Limited (429)", f"Retrying in {sleep_time:.2f}s... (Attempt {attempt+1}/{retries})")
                        time.sleep(sleep_time)
                    else:
                        raise ex

            output_text = response.text
            self.log("LLM Response Received", f"Output length: {len(output_text)}")
            return output_text
            
        except Exception as e:
            error_msg = f"Error calling Gemini in agent {self.name}: {str(e)}"
            self.log("LLM Error", error_msg)
            return f"Error: {error_msg}"

    def get_mock_response(self, user_prompt: str) -> str:
        """Provides fallback mock responses when Gemini is offline."""
        return (
            f"Mock response from {self.name} ({self.role}):\n"
            "This is a placeholder response because no active GEMINI_API_KEY was found. "
            "Configure your API key in the sidebar or a .env file to enable live reasoning and analysis."
        )
