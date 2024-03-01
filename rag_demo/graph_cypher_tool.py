from langchain.tools import tool
from graph_cypher_chain import get_results

@tool("graph-cypher-tool")
def graph_cypher_tool(query:str) -> str:
    """
    Useful when answer requires calculating numerical answers like aggregations.
    Use when question asks for a count or how many.
    Use full question as input.
    Do not call this tool more than once.
    Do not call another tool if this returns results.
    """
    return get_results(query)