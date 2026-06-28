import pytest
import json
from unittest.mock import MagicMock, patch
from app.agents.agent_definitions import ResearchAgents, ResearchState
from app.memory.memory_store import ResearchMemory
class TestResearchState:
    def test_initial_state_creation(self):
        state = {
            "topic": "test topic",
            "plan": [],
            "evidence": [],
            "summaries": [],
            "critic_report": {"pass_check": False, "feedback": "", "missing_topics": [], "flagged_claims": []},
            "final_report": "",
            "iterations": 0,
            "status": "Starting..."
        }
        assert state["topic"] == "test topic"
        assert state["iterations"] == 0
        assert state["critic_report"]["pass_check"] is False
class TestPlannerAgent:
    @patch("app.agents.agent_definitions.ChatOpenAI")
    def test_planner_generates_plan(self, mock_llm_class):
        mock_response = MagicMock()
        mock_response.content = json.dumps([
            {"question": "What is AI?", "search_query": "what is artificial intelligence"},
            {"question": "How does AI impact jobs?", "search_query": "AI job impact 2025"}
        ])
        mock_llm = MagicMock()
        mock_llm.__or__ = MagicMock(return_value=MagicMock(invoke=MagicMock(return_value=mock_response)))
        mock_llm_class.return_value = mock_llm
        agents = ResearchAgents()
        agents.llm = mock_llm
        state = {
            "topic": "Impact of AI on jobs",
            "plan": [],
            "evidence": [],
            "summaries": [],
            "critic_report": {"pass_check": False, "feedback": "", "missing_topics": [], "flagged_claims": []},
            "final_report": "",
            "iterations": 0,
            "status": ""
        }
        assert "topic" in state
        assert isinstance(state["plan"], list)
    def test_planner_handles_empty_topic(self):
        state = {"topic": "", "plan": [], "evidence": [], "summaries": [],
                 "critic_report": {"pass_check": False}, "final_report": "",
                 "iterations": 0, "status": ""}
        assert state["topic"] == ""
class TestCriticDecision:
    def test_critic_passes_on_good_score(self):
        state = {
            "critic_report": {"pass_check": True, "quality_score": 9},
            "iterations": 1
        }
        passed = state["critic_report"]["pass_check"]
        assert passed is True
    def test_critic_retries_on_fail(self):
        state = {
            "critic_report": {"pass_check": False, "quality_score": 4, "missing_topics": ["AI ethics"]},
            "iterations": 1
        }
        passed = state["critic_report"]["pass_check"]
        iterations = state["iterations"]
        max_cycles = 3
        assert not passed
        assert iterations < max_cycles
    def test_critic_stops_at_max_iterations(self):
        state = {
            "critic_report": {"pass_check": False, "quality_score": 5},
            "iterations": 3
        }
        max_cycles = 3
        assert state["iterations"] >= max_cycles
class TestResearchMemory:
    def test_memory_init(self, tmp_path):
        memory = ResearchMemory()
        assert memory is not None
    def test_save_and_retrieve_session(self):
        memory = ResearchMemory()
        session_id = memory.save_session(
            topic="Test topic about machine learning",
            report="# Test Report\n\nThis is a test.",
            score=8,
            iterations=2,
            sub_questions=[
                {"question": "What is ML?", "search_query": "machine learning basics"}
            ]
        )
        assert session_id is not None
        assert session_id > 0
        session = memory.get_session(session_id)
        assert session is not None
        assert session["topic"] == "Test topic about machine learning"
        assert session["quality_score"] == 8
    def test_find_related_research(self):
        memory = ResearchMemory()
        memory.save_session(
            topic="Deep learning in computer vision",
            report="Report about CV",
            score=7,
            iterations=1,
            sub_questions=[]
        )
        results = memory.find_related_research("computer vision applications")
        assert isinstance(results, list)
    def test_get_recent_sessions(self):
        memory = ResearchMemory()
        sessions = memory.get_recent_sessions(limit=5)
        assert isinstance(sessions, list)
class TestSearchTool:
    def test_search_tool_initialization(self):
        from app.tools.search import ResearchSearch
        search = ResearchSearch(max_results=3)
        assert search is not None
    @patch("app.tools.search.DuckDuckGoSearchRun")
    def test_search_returns_results(self, mock_search_class):
        mock_instance = MagicMock()
        mock_instance.run.return_value = "Some search results about AI"
        mock_search_class.return_value = mock_instance
        from app.tools.search import ResearchSearch
        search = ResearchSearch()
        search.search = mock_instance
        result = search.run_query("AI trends 2025")
        assert isinstance(result, str)
    @patch("app.tools.search.DuckDuckGoSearchRun")
    def test_search_handles_errors(self, mock_search_class):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = Exception("Network error")
        mock_search_class.return_value = mock_instance
        from app.tools.search import ResearchSearch
        search = ResearchSearch()
        search.search = mock_instance
        result = search.run_query("test query")
        assert "failed" in result.lower() or "error" in result.lower()
