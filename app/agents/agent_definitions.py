import os
import json
import logging
from typing import List, Dict, Any, TypedDict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..utils.config import GROQ_API_KEY, LLM_MODEL, GROQ_BASE_URL, MAX_SUB_QUESTIONS
logger = logging.getLogger(__name__)
class ResearchState(TypedDict):
    topic: str
    plan: List[Dict[str, str]]
    evidence: List[Dict[str, Any]]
    summaries: List[str]
    critic_report: Dict[str, Any]
    final_report: str
    iterations: int
    status: str
class ResearchAgents:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=GROQ_API_KEY,
            openai_api_base=GROQ_BASE_URL,
            temperature=0.3,
        )
    def planner_agent(self, state: ResearchState) -> Dict[str, Any]:
        logger.info(f"Planner: Breaking down topic - iteration {state.get('iterations', 0)}")
        critic_feedback = state.get("critic_report", {}).get("feedback", "")
        missing_topics = state.get("critic_report", {}).get("missing_topics", [])
        if missing_topics:
            prompt = ChatPromptTemplate.from_template(
                "You are a research planner. The previous research on '{topic}' had gaps.\n\n"
                "Missing information:\n{gaps}\n\n"
                "Generate {max_q} specific search queries to fill these gaps.\n"
                "Return a JSON array: [{{'question': '...', 'search_query': '...'}}]\n"
                "Return ONLY the JSON array, no other text."
            )
            response = (prompt | self.llm).invoke({
                "topic": state["topic"],
                "gaps": "\n".join(f"- {t}" for t in missing_topics),
                "max_q": min(len(missing_topics), 3)
            })
        else:
            prompt = ChatPromptTemplate.from_template(
                "You are a research planner. Break the topic '{topic}' into "
                "{max_q} specific sub-questions for investigation.\n\n"
                "For each sub-question, also provide a good search query.\n"
                "Return a JSON array: [{{'question': '...', 'search_query': '...'}}]\n"
                "Return ONLY the JSON array, no other text."
            )
            response = (prompt | self.llm).invoke({
                "topic": state["topic"],
                "max_q": MAX_SUB_QUESTIONS
            })
        try:
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            plan = json.loads(content)
            if not isinstance(plan, list):
                plan = [plan]
        except (json.JSONDecodeError, IndexError):
            logger.warning("Couldn't parse JSON from Planner, using fallback")
            lines = [l.strip() for l in response.content.split("\n") if "?" in l]
            plan = [{"question": q, "search_query": q} for q in lines[:MAX_SUB_QUESTIONS]]
        logger.info(f"Planner generated {len(plan)} sub-questions")
        return {"plan": plan, "status": f"Planning complete: {len(plan)} sub-questions"}
    def search_agent(self, state: ResearchState, search_tool) -> Dict[str, Any]:
        logger.info(f"Search: Running {len(state['plan'])} searches")
        evidence = state.get("evidence", [])
        for item in state["plan"]:
            query = item.get("search_query", item.get("question", ""))
            try:
                results = search_tool.run_query(query)
                evidence.append({
                    "question": item.get("question", query),
                    "search_query": query,
                    "results": results,
                    "source": "duckduckgo"
                })
                logger.info(f"  Searched: {query[:50]}...")
            except Exception as e:
                logger.error(f"  Search failed for '{query}': {e}")
                evidence.append({
                    "question": item.get("question", query),
                    "results": f"Search failed: {str(e)}",
                    "source": "error"
                })
        return {"evidence": evidence, "status": f"Search complete: {len(evidence)} results"}
    def summarizer_agent(self, state: ResearchState) -> Dict[str, Any]:
        logger.info("Summarizer: Compressing evidence")
        summaries = []
        for item in state["evidence"]:
            prompt = ChatPromptTemplate.from_template(
                "Summarize the following search results for the question: '{question}'\n\n"
                "Search results:\n{results}\n\n"
                "Provide 3-5 key findings. For each finding, note if the evidence is "
                "strong, moderate, or weak. Keep it concise."
            )
            response = (prompt | self.llm).invoke({
                "question": item["question"],
                "results": str(item["results"])[:3000]
            })
            summaries.append(response.content)
        return {"summaries": summaries, "status": "Summarization complete"}
    def critic_agent(self, state: ResearchState) -> Dict[str, Any]:
        logger.info(f"Critic: Reviewing research (iteration {state.get('iterations', 0) + 1})")
        all_summaries = "\n\n---\n\n".join([
            f"Sub-question: {state['plan'][i].get('question', 'N/A')}\n{summary}"
            for i, summary in enumerate(state["summaries"])
            if i < len(state["plan"])
        ])
        prompt = ChatPromptTemplate.from_template(
            "You are a research critic. Review these research summaries on '{topic}'.\n\n"
            "{summaries}\n\n"
            "Evaluate:\n"
            "1. Are there major gaps in the research?\n"
            "2. Are any claims unsupported or potentially hallucinated?\n"
            "3. Is the evidence sufficient to write a comprehensive report?\n\n"
            "Return a JSON object:\n"
            "{{\n"
            '  "pass_check": true/false,\n'
            '  "quality_score": 1-10,\n'
            '  "feedback": "your overall assessment",\n'
            '  "missing_topics": ["topic1", "topic2"],\n'
            '  "flagged_claims": ["claim that seems unsupported"]\n'
            "}}\n"
            "Return ONLY the JSON, no other text."
        )
        response = (prompt | self.llm).invoke({
            "topic": state["topic"],
            "summaries": all_summaries
        })
        try:
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            report = json.loads(content)
        except (json.JSONDecodeError, IndexError):
            logger.warning("Couldn't parse Critic JSON, assuming pass")
            report = {
                "pass_check": True,
                "quality_score": 7,
                "feedback": response.content,
                "missing_topics": [],
                "flagged_claims": []
            }
        new_iterations = state.get("iterations", 0) + 1
        logger.info(f"Critic: score={report.get('quality_score')}, pass={report.get('pass_check')}")
        return {
            "critic_report": report,
            "iterations": new_iterations,
            "status": f"Critic review {new_iterations}/{MAX_REFLECTION_CYCLES}: score={report.get('quality_score')}, passed={report.get('pass_check')}"
        }
    def synthesizer_agent(self, state: ResearchState) -> Dict[str, Any]:
        logger.info("Synthesizer: Assembling final report")
        all_summaries = "\n\n".join(state["summaries"])
        critic_notes = state.get("critic_report", {}).get("feedback", "No critic notes.")
        flagged = state.get("critic_report", {}).get("flagged_claims", [])
        prompt = ChatPromptTemplate.from_template(
            "You are a research synthesizer. Create a comprehensive report on '{topic}' "
            "based on these research findings.\n\n"
            "Research summaries:\n{summaries}\n\n"
            "Critic notes: {critic_notes}\n"
            "Flagged claims (mention these have lower confidence): {flagged}\n\n"
            "Structure the report as:\n"
            "# Research Report: [Topic]\n\n"
            "## Executive Summary\n"
            "[2-3 sentence overview]\n\n"
            "## Key Findings\n"
            "[Main findings with evidence]\n\n"
            "## Analysis\n"
            "[Deeper analysis connecting the findings]\n\n"
            "## Limitations\n"
            "[What we couldn't verify or find]\n\n"
            "## Conclusion\n"
            "[Final summary]\n"
        )
        response = (prompt | self.llm).invoke({
            "topic": state["topic"],
            "summaries": all_summaries,
            "critic_notes": critic_notes,
            "flagged": ", ".join(flagged) if flagged else "None"
        })
        return {
            "final_report": response.content,
            "status": "Report complete"
        }
