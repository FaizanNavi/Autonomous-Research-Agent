# 🧪 Testing Guide — Autonomous Research Agent

## Test 1: Graph Compilation (No API key needed)
```bash
python -c "from app.agents.orchestrator import ResearchOrchestrator; o = ResearchOrchestrator(); print('Graph compiled! Nodes:', list(o.workflow.get_graph().nodes.keys()))"
```

## Test 2: Search Tool (No API key needed)
```bash
python -c "from app.tools.search import ResearchSearch; s = ResearchSearch(); print(s.run_query('AI trends 2025')[:300])"
```

## Test 3: Full Research Run (Needs GROQ_API_KEY)
```bash
uvicorn app.main:app --reload --port 8003

# In another terminal:
curl -X POST http://localhost:8003/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "How are companies using AI agents in production?"}'
```

## What to Show in Interviews
1. **Reflection loop**: Show the logs where Critic sends it back for more research
2. **Structured output**: Show the JSON critic report with quality score
3. **Graph structure**: Explain the LangGraph state machine
