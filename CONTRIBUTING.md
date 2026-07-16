# Contributing to EarningsIQ

Thank you for your interest in contributing to **EarningsIQ**! We welcome bug fixes, documentation updates, design enhancements, and feature requests. Following these guidelines ensures a smooth collaboration process for everyone.

---

## 🛠️ Local Environment Setup

### Prerequisites
* Python 3.10, 3.11, or 3.12
* Git

### Step-by-Step Installation
1. **Fork & Clone** the repository:
   ```bash
   git clone https://github.com/YourUsername/earnings_iq.git
   cd earnings_iq
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and paste your GEMINI_API_KEY
   ```

---

## 🧪 Running the Test Suite

We maintain 100% pass rates on our test suite. Before submitting any pull requests, run `pytest` locally to confirm no regressions:
```bash
python -m pytest tests/
```

---

## 📝 Coding Standards

To maintain code quality comparable to top open-source projects:
* **Style Guide**: Follow PEP 8 guidelines.
* **Type Hints**: Include type hints for all public functions and classes.
* **Docstrings**: Write docstrings for all classes and methods in the Google Docstring format.
* **Linting**: Ensure your code is free of warnings and unused imports.

---

## 💬 Semantic Commit Messages

We use semantic commit messages to track changes and automate versioning. Please format your commits as follows:
* `feat: ` New user-facing feature additions.
* `fix: ` Code fixes (e.g., math verification corrections).
* `docs: ` Documentation additions or changes.
* `style: ` Visual and CSS adjustments (non-functional changes).
* `refactor: ` Code reorganizations that neither fix bugs nor add features.
* `test: ` Adding or updating unit tests.
