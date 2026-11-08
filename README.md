# LLMOps Clinical Trial Protocol Agent

An enterprise-grade LLMOps pipeline and agentic system built with LangChain, LangGraph, and FastAPI designed for automated clinical trial protocol extraction, multi-stage validation, human-in-the-loop (HIL) review, and AI-driven patient matching.

---

## Project Structure

```text
llmops-clinical-trial-agent/
├── .github/workflows/ci_cd.yml          # GitHub Actions CI/CD and evaluation gates
├── configs/
│   ├── alert.rules.yml                  # Prometheus alerting rules for agent health
│   └── prometheus.yml                   # Prometheus metrics scrape configuration
├── data/protocols/                      # Source clinical trial protocol documents
├── prompts/                             # Extraction prompt templates (v1, v2)
├── scripts/
│   ├── generate_traffic.py              # Synthetic traffic generator for metrics testing
│   ├── run_agent.py                     # CLI script for running end-to-end pipeline
│   ├── test_pipeline.py                 # Unit tests for guardrails and evaluators
│   └── web_app.py                       # FastAPI production server & HIL dashboard
├── src/
│   ├── data/indexed_trials.json         # Core trial data persistence store
│   ├── database.py                      # Secure JSON database management layer
│   ├── evaluation.py                    # Claude-powered faithfulness & QA evaluation
│   ├── guardrails.py                    # Input sanitization and clinical boundary validation
│   ├── matching_engine.py               # Patient eligibility matching against trial criteria
│   ├── prompts.py                       # Dynamic prompt builder utilities
│   ├── schemas.py                       # Pydantic data schemas & LangGraph state definitions
│   ├── tools.py                         # PDF parser, OCR fallback, and ChromaDB RAG tooling
│   └── workflow.py                      # LangGraph state machine orchestrator
├── tests/
│   ├── evals/run_eval.py                # Golden dataset automated evaluation runner
│   └── golden_dataset/cases.json        # Ground-truth test cases for extraction accuracy
├── docker-compose.yml                   # Prometheus & Grafana monitoring stack
├── Dockerfile                           # Multi-stage production container build
└── requirements.txt                     # Python dependencies

```

---

## Deep Architectural Breakdown & Data Flow

The system operates as an end-to-end automated data engineering pipeline for clinical research, bridging document parsing, LLM-based extraction, human review gates, and patient matching.

### 1. LangGraph Agent State Machine (`src/workflow.py`)

The pipeline execution is modeled as a deterministic state machine using LangGraph:

* **Extractor Node (`extractor`):** Triggers document ingestion, OCR fallback when needed, vector embedding via HuggingFace, ChromaDB retrieval, and Anthropic Claude-powered structured extraction.


* **Validator Node (`validator`):** Inspects extracted inclusion and exclusion criteria to ensure lists are populated and structurally sound.


* **Human Review Node (`human_review`):** Evaluates extraction confidence and holds unverified or empty criteria in a pending state (`PENDING_HIL_REVIEW`) awaiting clinical sign-off.


* **Indexer Node (`indexer`):** Persists approved structured criteria into the secure trial database so downstream patient matching engines can query them.



### 2. RAG & Document Processing (`src/tools.py`)

* Handles complex, multi-page clinical protocol PDFs by attempting direct text extraction via `pypdf`.


* Automatically triggers an OCR fallback (`pdf2image` and `pytesseract`) if scanned pages lack extractable text.


* Splits documents using `RecursiveCharacterTextSplitter`, computes local vector embeddings (`all-MiniLM-L6-v2`), and indexes chunks in **ChromaDB** for semantic retrieval.



### 3. Guardrails & Faithfulness Evaluation (`src/guardrails.py`, `src/evaluation.py`)

* **Sanitization & Clinical Boundaries:** Strips null bytes and control characters while scanning for ungrounded claims or hallucinated constraints (e.g., "cure-all" or "guaranteed" therapies).


* **Production Evaluator:** Audits extracted criteria against source protocol text using Claude, computing confidence scores and detailed faithfulness critiques.



---

## Human-in-the-Loop (HIL) Clinical Workflow

To ensure regulatory compliance and medical accuracy, the FastAPI web application (`src/web_app.py`) provides an asynchronous review workflow:

1. **Upload & Analysis:** Uploaded protocol PDFs (`/upload-and-analyze/`) run through the LangGraph pipeline.


2. **Pending Queue:** If extractions require clinical verification, states are cached in an in-memory review dictionary (`PENDING_REVIEWS`).


3. **Expert Sign-Off:** Clinical experts query pending reviews (`/protocols/pending-reviews`) and submit approvals or rejections (`/protocols/{trial_id}/review`) with custom reviewer notes. Approvals trigger downstream database indexing automatically.



---

## Observability & LLMOps Monitoring

The application integrates production monitoring instrumentation:

* **Prometheus Middleware:** Automatically records HTTP request counts (`http_requests_total`) and latency histograms (`http_request_duration_seconds`) across all endpoints.


* **Scrape Endpoint:** Exposes metrics securely at `/metrics`.


* **Alerting Rules (`configs/alert.rules.yml`):** Automatically triggers alerts if the `clinical-trial-agent` target goes down for over 1 minute or if the 5xx error rate exceeds 5% over a 2-minute window.


* **Grafana & Prometheus Stack:** Easily spun up via Docker Compose for real-time visualization.



---

## Getting Started & Installation

### Prerequisites & Setup

Clone the repository and set up your virtual environment:

```bash
git clone https://github.com/your-org/llmops-clinical-trial-agent.git
cd llmops-clinical-trial-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

```

Configure your `.env` file with required API keys and tracing configurations:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
HF_TOKEN=your_huggingface_token
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key

```

### Running the Pipeline via CLI

Execute the end-to-end clinical protocol extraction and patient matching simulation:

```bash
python scripts/run_agent.py --pdf protocols/trial_protocol_104xb.pdf
```

### Launching the Web Server
Start the FastAPI application:
```bash
python scripts/web_app.py
```
* **Interactive API Docs:** `http://localhost:8000/docs`
* **Prometheus Metrics:** `http://localhost:8000/metrics`

---

## 🐳 Docker & Monitoring Deployment

Run the multi-stage container build or spin up the full observability stack with Docker Compose:

```bash
# Build production container
docker build -t clinical-trial-agent .

# Spin up Prometheus and Grafana
docker-compose up -d
```

* **Prometheus UI:** `http://localhost:9090`
* **Grafana Dashboard:** `http://localhost:3000` (Default credentials: `admin` / `admin`)

---

## License

This project is licensed under the MIT License:

```text
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```