from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool

from rag_vector_only import get_results

@tool("vector-tool")
def vector_graph(query:str) -> str:
    """Tool for retrieving SEC filing information on companies and the firms that filed them using a vector similarity search within a Neo4j knowledge graph. Useful for finding facts or suggesting possible Companies based on information within filing data.
    """
    result = get_results(query)
    return result.get("result", None)