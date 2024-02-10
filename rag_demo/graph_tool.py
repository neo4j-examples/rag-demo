from langchain.tools import tool
from graph_chain import get_results

@tool("graph-tool")
def graph_tool(query:str) -> str:
    """Tool for returning aggregations of Manager or Company data or if answer is dependent on relationships between a Company and other objects. Uses Cypher generated from a Neo4j graph schema to find an anwer.
    """
    return get_results(query)