from langchain.tools import tool
from rag_demo.chains.vector_graph_chain import get_results

@tool
def vector_graph_tool(query:str) -> str:
    """Tool for finding Companies and owners of companies based on keyword similarity. Uses a vector similarity search and a retrieval query within a Neo4j knowledge graph. Useful for finding facts or suggesting possible Companies based on information within filing data.
    """
    return get_results(query)