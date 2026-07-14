# 🔬 Autonomous Research Agent

A 5-agent AI system that researches any topic autonomously using a **LangGraph reflection loop**. The Critic agent reviews the research quality and can send it back for another round — up to 3 cycles — so the output keeps improving.

## 🎯 What This Does
Give it a topic → it breaks it into sub-questions, searches the web, summarizes findings, critically reviews them for gaps, and assembles a structured research report.

**Key engineering feature:** The reflection loop. The Critic agent evaluates the research and routes back to the Planner if there are gaps. This is NOT a simple linear chain — it's a state machine that improves its own output.

## 🏗️ Architecture

```
User Topic
     │
     ▼
┌─────────────┐
│  Planner    │ ← Breaks topic into 5-8 sub-questions
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Search ×N  │ ← DuckDuckGo (free, no API key)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Summarizer  │ ← Compresses evidence into key findings
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──── retry (if gaps found)
│   Critic    │ ────►│
└──────┬──────┘     └──── pass (if good enough)
       │
       ▼
┌─────────────┐
│ Synthesizer │ ← Assembles final structured report
└─────────────┘
```

The Critic → Planner loop runs max 3 times to prevent infinite loops.

## 🛠️ Tech Stack
| Component | Technology |
|-----------|-----------|
| LLM | Groq (Llama 3.3 70B) - free tier |
| Orchestration | LangGraph state machine |
| Search | DuckDuckGo (free, no API key) |
| Framework | FastAPI (async) |
| Memory | SQLite (research history) |
| LLM Client | LangChain + OpenAI-compatible |

## 📁 Project Structure
```
P3-Autonomous-Research/
├── app/
│   ├── __init__.py
│   ├── main.py                    ← FastAPI server
│   ├── agents/
│   │   ├── orchestrator.py        ← LangGraph state machine
│   │   └── agent_definitions.py   ← All 5 agent implementations
│   ├── tools/
│   │   └── search.py              ← DuckDuckGo search wrapper
│   ├── memory/
│   │   └── memory_store.py        ← SQLite research history
│   └── utils/
│       └── config.py              ← Centralized config
├── tests/
│   └── test_agents.py             ← Unit tests
├── data/                          ← Local sqlite DB storage
├── frontend/                      ← Production HTML/JS frontend (for dev/presentation)
├── streamlit_app.py               ← Quick Streamlit UI for internal testing
├── .env.example
├── .gitignore
├── requirements.txt
├── TESTING.md
└── README.md
```

## 🚀 Quick Start

### 1. Install uv (if not already installed)
```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Set up environment
```bash
cd P3-Autonomous-Research
cp .env.example .env
# Edit .env and add your GROQ_API_KEY (free at console.groq.com)
```

### 3. Install dependencies
```bash
uv sync
```
This creates a `.venv/` and installs all packages from `pyproject.toml` automatically.

### 4. Run everything with a single command 🎉
```bash
uv run python run.py
```

This starts **both** the FastAPI backend (port 8003) and the HTML frontend (port 3000) together. Press `Ctrl+C` once to shut everything down.

| Service | URL |
|---------|-----|
| Backend API | `http://localhost:8003` |
| API Docs | `http://localhost:8003/docs` |
| Frontend | `http://localhost:3000` |

---

## 🖥️ Run Options

### Default — Backend + HTML Frontend
```bash
uv run python run.py
```

### Backend Only
```bash
uv run python run.py --no-frontend
```

### Backend + Streamlit UI
```bash
uv run python run.py --streamlit
```
Opens Streamlit at `http://localhost:8501` with:
- 📝 **Topic chat input** — enter any research topic
- 🔄 **Reflection loop explanation sidebar** — understand how agents iterate
- 📚 **Example topics** — one-click topic presets for quick testing
- 📊 **Agent metadata expander** — view reflection cycles, critic score, and final status

### Manual (individual services)
```bash
# Terminal 1 — Backend
uv run uvicorn app.main:app --port 8003 --reload

# Terminal 2 — Frontend
cd frontend && python -m http.server 3000

# Terminal 3 — Streamlit (optional)
uv run streamlit run streamlit_app.py
```

## 📐 API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /research | Research any topic → structured report |
| GET | /health | Health check |

## 🔄 The Reflection Loop — How It Works

1. **Planner** breaks topic into 5 sub-questions
2. **Search** agents run DuckDuckGo queries for each
3. **Summarizer** compresses results into key findings
4. **Critic** reviews everything and decides:
   - ✅ Pass → move to Synthesizer
   - ❌ Fail → sends `missing_topics[]` back to Planner
5. **Planner** generates NEW questions targeting only the gaps
6. Steps 2-4 repeat (max 3 cycles)
7. **Synthesizer** writes the final structured report

## 🧪 Running Tests
```bash
pytest tests/ -v
```


