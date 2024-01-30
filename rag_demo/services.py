
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.llms import Ollama

from langchain_community.graphs import Neo4jGraph

llm = ChatOpenAI(temperature=0)
# llm = Ollama(model="llama2")

embedding_model = OpenAIEmbeddings()

graph = Neo4jGraph()

graph.query("CREATE FULLTEXT INDEX company IF NOT EXISTS FOR (com:Company) ON EACH [com.all_names]")