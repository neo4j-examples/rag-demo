from langchain.tools import tool
from graph_chain import get_results

@tool("graph-tool")
def graph_tool(query:str) -> str:
    """Tool for returning aggregations of Manager or Company or Industry data or if answer is dependent on relationships between a Company and other objects. Use this tool second and to verify results of vector-graph-tool.
    """
    return get_results(query)