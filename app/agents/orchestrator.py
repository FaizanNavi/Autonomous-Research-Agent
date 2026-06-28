import logging
from langgraph.graph import StateGraph, END
from .agent_definitions import ResearchAgents, ResearchState
from ..tools.search import ResearchSearch
from ..utils.config import MAX_REFLECTION_CYCLES
logger = logging.getLogger(__name__)
class ResearchOrchestrator:
    def __init__(self):
        self.agents = ResearchAgents()
        self.search_tool = ResearchSearch()
        self.workflow = self._create_workflow()
    def _create_workflow(self):
        workflow = StateGraph(ResearchState)
        workflow.add_node("plan", self.agents.planner_agent)
        workflow.add_node("search", self._search_node)
        workflow.add_node("summarize", self.agents.summarizer_agent)
        workflow.add_node("criticize", self.agents.critic_agent)
        workflow.add_node("synthesize", self.agents.synthesizer_agent)
        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "search")
        workflow.add_edge("search", "summarize")
        workflow.add_edge("summarize", "criticize")
        workflow.add_conditional_edges(
            "criticize",
            self._should_continue,
            {
                "retry": "plan",
                "finish": "synthesize"
            }
        )
        workflow.add_edge("synthesize", END)
        return workflow.compile()
    def _search_node(self, state: ResearchState):
        return self.agents.search_agent(state, self.search_tool)
    def _should_continue(self, state: ResearchState) -> str:
        critic_report = state.get("critic_report", {})
        passed = critic_report.get("pass_check", True)
        iterations = state.get("iterations", 0)
        if passed:
            logger.info("Critic approved - moving to synthesis")
            return "finish"
        if iterations >= MAX_REFLECTION_CYCLES:
            logger.info(f"Max reflection cycles ({MAX_REFLECTION_CYCLES}) reached - moving to synthesis")
            return "finish"
        logger.info(f"Critic wants more research (iteration {iterations}/{MAX_REFLECTION_CYCLES})")
        return "retry"
    def run(self, topic: str) -> dict:
        initial_state = {
            "topic": topic,
            "plan": [],
            "evidence": [],
            "summaries": [],
            "critic_report": {"pass_check": False, "feedback": "", "missing_topics": [], "flagged_claims": []},
            "final_report": "",
            "iterations": 0,
            "status": "Starting research..."
        }
        logger.info(f"Starting research on: {topic}")
        result = self.workflow.invoke(initial_state)
        logger.info(f"Research complete after {result.get('iterations', 0)} iteration(s)")
        return result
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    orchestrator = ResearchOrchestrator()
    print("Research Graph compiled successfully!")
    print("Nodes:", list(orchestrator.workflow.get_graph().nodes.keys()))
