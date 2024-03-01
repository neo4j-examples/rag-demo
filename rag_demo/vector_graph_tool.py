from langchain.tools import tool
from vector_graph_chain import get_results

@tool("vector-graph-tool")
def vector_graph_tool(query:str) -> str:
    """
    Useful when answer requires specific information about companies, managers, or industries.
    Use when question asks for which companies, managers, or industries.
    Use full question as input.
    Do not call this tool more than once.
    Do not call another tool if this returns results.
    """
    return get_results(query)