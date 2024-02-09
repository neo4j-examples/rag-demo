from langchain.tools import tool
from rag_demo.chains.vector_chain import get_results

@tool
def vector_only_tool(query:str) -> str:
    """Tool for finding facts or Companies based on information within filing data. Uses a vector similarity search only. Best for when other tools are unable to return an answer.
    """
    return get_results(query)