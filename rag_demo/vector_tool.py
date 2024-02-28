from langchain.tools import tool
from vector_chain import get_results

@tool("vector-tool")
def vector_tool(query:str) -> str:
    """For finding facts or Companies based on information within filing data. Uses a vector similarity search only. Only use this tool if no answer from others. Do not call another tool after this one.
    """
    return get_results(query)