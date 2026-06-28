mit
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
├── .env.example
├── .gitignore
├── requirements.txt
├── TESTING.md
└── README.md
```

## 🚀 Quick Start

### 1. Install dependencies
```bash
cd P3-Autonomous-Research
pip install -r requirements.txt
```

### 2. Set up environment
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY (free at console.groq.com)
```

### 3. Start the server
```bash
uvicorn app.main:app --reload --port 8003
```

### 4. Try it
Open http://localhost:8003/docs for interactive API docs, or:

```bash
curl -X POST http://localhost:8003/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "Impact of AI on job markets in 2025"}'
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

## 📝 Resume Bullet
> "Built Autonomous Research Agent with LangGraph supervisor pattern — 5 agents (Planner, Search×N, Summarizer, Critic, Synthesizer) with a 3-cycle reflection loop. Critic verifies citations by cross-checking source evidence, routes missing topics back to Planner for targeted re-search. SQLite memory tracks research history across sessions."

## 📄 License
MIT
