# Writex: Academic Report Engine

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

Writex is an Enterprise-grade Academic Report Compilation Engine. It acts as an intelligent intermediary, scanning raw Developer Source Code (`.zip`) and utilizing Cloud LLMs (Groq Llama-3 70B) to statically analyze and synthesize a structurally perfect, university-compliant B.Tech Academic Report in `.docx` format.

## 🚀 Key Features

* **In-Memory AST Parsing:** Upload a zipped codebase. The engine natively traverses the code strictly in constrained RAM (`io.BytesIO`)—no proprietary source code ever touches the physical disk.
* **Deterministic Concurrency:** Generating a 6-chapter structural report usually takes LLMs 5-10 minutes. Writex uses a deeply managed `ThreadPoolExecutor` array to fetch independent sub-sections in parallel, dropping total execution time to **under 45 seconds**.
* **Zero-Trust Data Sanitization:** Before the Abstract Syntax Tree (AST) context is sent to the Cloud LLM, a localized security module aggressively regex-scrubs any hardcoded API Keys, AWS Tokens, or PII (Emails).
* **Native Microsoft Word Structuring:** Does not rely on generic markdown conversion. Writex generates native Word XML elements (`w:sdt`), natively bootstrapping Document Table of Contents, Lists of Figures, and embedded metadata properties.
* **Hallucination Constraints:** Writex employs strict, programmatically managed "Diagram Bans" for non-technical chapters, mathematically stopping the LLM from trying to structure placeholders in theoretical chapters.

## 🛠️ Technology Stack

* **Frontend Engine:** Streamlit
* **Native LLM Integration:** Groq (Llama-3.3-70b-versatile)
* **Ast/Code Parsing:** Python `ast`, Native Regex
* **Document Compilation:** `python-docx`
* **Static Typing & Quality:** `mypy`, `flake8`, `black`, `bandit`, `pytest`

## 📦 Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/writex.git
   cd writex
   ```

2. **Create a Virtual Environment (Recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory and add your Groq API Key (Or inject it directly in the UI):
   ```ini
   GROQ_API_KEY=your_groq_key_here
   ```

5. **Run the Application:**
   ```bash
   streamlit run src/app.py
   ```

## 🛡️ Security & Testing

Writex was built with Enterprise resilience in mind. The entire `src/` directory passes `flake8`, `mypy` (strict mode), and `bandit` with 0 security vulnerabilities.
To run the internal unit testing suite locally:

```bash
pytest test/ tests/
```

## 🤝 Contributing
Contributions are absolutely welcome. Please ensure any new modules pass `black` formatting and do not degrade the strict AST parsing pipeline. 

## 📝 License
This project is licensed under the MIT License.
