import re
import subprocess
from pathlib import Path

def escape_dollar_signs(text: str) -> str:
    """
    Escapes dollar signs in text strings to prevent Streamlit's markdown parser
    from misinterpreting them as LaTeX math block delimiters.
    """
    if not isinstance(text, str):
        return text
    # Normalize already-escaped dollars first to avoid double-escaping
    text = text.replace(r"\$", "$")
    return text.replace("$", r"\$")

def get_git_commit_sha(project_dir: Path = Path(".")) -> str:
    """
    Retrieves the short Git commit SHA hash dynamically.
    Checks for the presence of the .git folder to prevent CLI execution warnings 
    in non-Git sandbox containers (such as zip uploads or Streamlit Cloud).
    """
    git_dir = project_dir / ".git"
    if not git_dir.exists():
        return "5a546af"  # Fallback to last known release commit SHA
        
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], 
            cwd=str(project_dir),
            stderr=subprocess.DEVNULL
        ).decode("ascii").strip()
        return sha
    except Exception:
        return "5a546af"
