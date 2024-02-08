from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool

from rag_graph import get_results

@tool("graph-tool")
def graph_cypher(query:str) -> str:
    """Tool for retrieving SEC filing information on companies and the firms that filed them using a Neo4j knowledge graph using Cypher. Great for returning aggregations of Manager or Company data. Don't use if wanting to search information within filing text details.
    """
    result = get_results(query)
    if result is None:
        return None
    
    return result.get("result", None)