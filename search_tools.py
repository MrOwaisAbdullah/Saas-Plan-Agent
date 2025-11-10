import os
from tavily import TavilyClient
from agents import function_tool
from typing import List, Optional, Dict, Any, Union

# Initialize Tavily Client
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable not set.")
tavily_client = TavilyClient(TAVILY_API_KEY)

# --- Tool Functions ---
@function_tool
def tavily_search_tool(query: str, max_results: int = 5, topic: str = "general", search_depth: str = "basic"):
    """
    Execute a Tavily search query and return structured results.

    Args:
        query (str): The search query.
        max_results (int, optional): Maximum number of results to return. Defaults to 5.
        topic (str, optional): The search topic ('general', 'news'). Defaults to "general".
        search_depth (str, optional): Depth of the search ('basic', 'advanced'). Defaults to "basic".
    """
    try:
        response = tavily_client.search(
            query,
            max_results=max_results,
            topic=topic,
            search_depth=search_depth
        )
        return {
            "query": response["query"],
            "results": [
                {
                    "url": result["url"],
                    "title": result["title"],
                    "content": result["content"],
                    "score": result["score"]
                }
                for result in response["results"]
            ],
            "response_time": response["response_time"]
        }
    except Exception as e:
        return {"error": str(e), "results": [], "response_time": None}

@function_tool
def tavily_extract_tool(urls: List[str], include_images: bool = False):
    """
    Extract content from a list of URLs using Tavily Extract API.

    Args:
        urls (List[str]): List of URLs to extract content from.
        include_images (bool, optional): Whether to include images in the extracted content. Default is False.
    """
    try:
        response = tavily_client.extract(urls=urls, include_images=include_images)
        
        # Check if response is a list (expected case)
        if isinstance(response, list):
            return [
                {
                    "url": result["url"],
                    "title": result.get("title", ""),
                    "content": result["content"],
                    "images": result.get("images", []) if include_images else []
                }
                for result in response
            ]
        else:
            # Handle case where response might be an error dictionary
            return {"error": f"Unexpected response format: {response}", "results": []}
    except Exception as e:
        return {"error": str(e), "results": []}

@function_tool
def tavily_crawl_tool(start_url: str, max_depth: int = 2, limit: int = 10, instructions: Optional[str] = None):
    """
    Crawl a website starting from a given URL using Tavily Crawl API.

    Args:
        start_url (str): The starting URL for the crawl.
        max_depth (int, optional): The maximum depth to crawl. Defaults to 2.
        limit (int, optional): The maximum number of pages to crawl. Defaults to 10.
        instructions (str, optional): Specific instructions for the crawler. Defaults to None.
    """
    try:
        response = tavily_client.crawl(
            url=start_url,
            max_depth=max_depth,
            limit=limit,
            instructions=instructions
        )
        return [
            {
                "url": result["url"],
                "raw_content": result["raw_content"]
            }
            for result in response["results"]
        ]
    except Exception as e:
        return {"error": str(e), "results": []}