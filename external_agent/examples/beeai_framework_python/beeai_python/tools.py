from beeai_framework.tools import tool
from tavily import TavilyClient

from beeai_python.settings import AppSettings


@tool
def search_web_tool(query: str) -> dict[str, str] | None:
    """

    Searches the web for the given query and returns the most relevant results.
    """

    client = TavilyClient(api_key=AppSettings.tavily_api_key)
    results = client.search(
        query,
        search_depth="advanced",
        max_results=10,
        include_images=False,
        include_answer=False,
    )
    return results
