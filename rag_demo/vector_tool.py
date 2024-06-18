from langchain.tools import tool
from vector_graph_chain import get_results


@tool("vector-tool")
def vector_tool(query: str) -> str:
    """
    For finding similar entities to the ones in the search query.
    Only use this tool if no answer from others.
    Do not call another tool after this one.
    """
    return get_results(query)
