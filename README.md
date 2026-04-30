# Writex: Automated Tech-Report Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Writex is an AI-powered documentation pipeline that transforms raw source code into strictly formatted academic reports (IEEE/APA). Built to automate the "last-mile" of technical documentation for students, hackathon teams, and researchers.

By analyzing your project code securely in-memory, Writex extracts the system architecture and implementation details to draft a comprehensive 6-chapter technical report, delivered as a ready-to-print Microsoft Word (`.docx`) file in under a minute.

![Writex Demo](https://via.placeholder.com/800x400.png?text=Drop+ZIP+%E2%86%92+Generate+Report+%E2%86%92+Download+.docx) *(Add a real GIF here!)*

## ✨ Key Features

*   **Code to Report Extraction:** Securely processes `src/` folder ZIPs in-memory. Code is parsed entirely in-memory and immediately discarded.
*   **Intelligent Restyling:** Upload a sample PDF or DOCX, and Writex will extract its structure and style to mimic it in your generated report.
*   **Deterministic Compilation:** Multi-pass compilation with automated validation gates ensures your report's structural integrity (headings, figures, and front matter).
*   **AI Resilience:** Built-in exponential backoff and jitter to handle API rate limits and 503 errors, ensuring reliable document generation.
*   **Lightning Fast:** Leveraging parallel processing and advanced caching to generate 30+ page reports in minutes.

## 🧠 Architecture Overview

Writex implements a multi-stage AI documentation pipeline that bridges deterministic static analysis with advanced LLM synthesis. By passing code through an AST Map-Reduce layer prior to generation, this architecture directly solves common LLM limitations—such as context dilution and hallucination—ensuring that all technical narratives are strictly grounded in your actual codebase.

![Writex Architecture Diagram](IMAGE%20FO%20RREADME.png)

### Key Design Principles

*   **Deterministic Parsing (AST):** Eliminates hallucination by extracting exact class structures, function footprints, and import graphs before any LLM involvement.
*   **Separation of Concerns:** System decoupled into distinct, purpose-built layers: User Interface, Analysis & Extraction, AI Orchestration, and Validation & Rendering.
*   **Validation & Auto-Healing:** Multi-pass validation gates ensure document structural integrity, automatically correcting heading hierarchies and formatting drift before output.
*   **Structured End-to-End Flow:** A seamless pipeline that securely translates raw code payloads into perfectly formatted, ready-to-print academic reports in-memory.

## 🛠️ Built With

*   **Frontend:** [Streamlit](https://streamlit.io/)
*   **AI Engine:** Groq (Llama 3.1 70B / 8B)
*   **Document Generation:** `python-docx`
*   **Formatting Automation:** Python XML parsing (plus optional VBScript/COM Interop on Windows for native MS Word updates).

## 🚀 How to Run It 

### Option 1: Using Docker (Recommended)

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/abhijitsvsk/WRITEX.git
   cd WRITEX
   ```

2. **Run with Docker Compose or basic Docker:**
   ```bash
   docker build -t writex-app .
   docker run -p 8501:8501 -e GROQ_API_KEY=your_key_here writex-app
   ```
   *Then access the app at `http://localhost:8501`.*

### Option 2: Local Setup

1. **Clone & Install Dependencies:**
   ```bash
   git clone https://github.com/abhijitsvsk/WRITEX.git
   cd WRITEX
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Create a `.env` file in the root directory and add your Groq API key:
   ```ini
   GROQ_API_KEY=your_key_here
   ```

3. **Launch the Application:**
   ```bash
   streamlit run src/app.py
   ```

## 🤝 Contributing

We welcome contributions! Especially around making cross-platform `.docx` manipulation completely native without Windows COM objects. 

Please see the [`CONTRIBUTING.md`](CONTRIBUTING.md) for details on how to get started, and feel free to pick up any issues tagged with `good first issue`.

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
