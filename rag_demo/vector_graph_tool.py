from langchain.tools import tool
from vector_chain import get_results

@tool("vector-graph-tool")
def vector_graph_tool(query:str) -> str:
    """For finding facts about Companies, Managers, or Industries based on information within filing data. Uses a vector similarity search with graph retrieval query. Use this tool first.
    """
    return get_results(query)