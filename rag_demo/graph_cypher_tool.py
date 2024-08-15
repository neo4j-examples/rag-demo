from langchain.tools import tool
from graph_cypher_chain import CypherChainClass

class GrpahCypherTool:
    def __init__(self):
        self.cypher_chain = CypherChainClass()

    def update_llm_key(self):
        self.cypher_chain.update_key()

#    @tool("graph-cypher-tool") - AMIT when working with agent this would need to be changed!!
    def run(self, tool_input:str) -> str:
        """
        Useful when answer requires calculating numerical answers like aggregations.
        Use when question asks for a count or how many.
        Use full question as input.
        Do not call this tool more than once.
        Do not call another tool if this returns results.
        """
        return (self.cypher_chain.get_results(tool_input))