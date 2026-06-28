import logging
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
logger = logging.getLogger(__name__)
class ResearchSearch:
    def __init__(self, max_results=5):
        self.wrapper = DuckDuckGoSearchAPIWrapper(max_results=max_results)
        self.search = DuckDuckGoSearchRun(api_wrapper=self.wrapper)
    def run_query(self, query: str) -> str:
        try:
            result = self.search.run(query)
            return result
        except Exception as e:
            logger.error(f"Search error for '{query}': {e}")
            return f"Search failed: {str(e)}"
if __name__ == "__main__":
    rs = ResearchSearch()
    result = rs.run_query("Latest AI agents trends 2025")
    print(result[:500])
