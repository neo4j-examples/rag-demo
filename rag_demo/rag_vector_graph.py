from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain.prompts.prompt import PromptTemplate
from langchain.llms.bedrock import Bedrock
from retry import retry
from timeit import default_timer as timer
import streamlit as st

from neo4j_driver import run_query
from json import loads, dumps
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.chains import RetrievalQAWithSourcesChain


EMBEDDING_MODEL = OpenAIEmbeddings()

url = st.secrets["NEO4J_URI"]
username = st.secrets["NEO4J_USERNAME"]
password = st.secrets["NEO4J_PASSWORD"]

graph = Neo4jGraph(
    url=url,
    username=username,
    password=password,
    sanitize = True
)

@retry(tries=5, delay=5)
def get_results(question):

    index_name = "document_text_openai_embeddings"
    node_property_name = "text_openai_embedding"
    url=st.secrets["NEO4J_URI"]
    username=st.secrets["NEO4J_USERNAME"]
    password=st.secrets["NEO4J_PASSWORD"]
    retrieval_query = """
    WITH node AS doc, score
    OPTIONAL MATCH (doc)<-[:OWNS_STOCK_IN]-(company:Company), (company)<-[:OWNS_STOCK_IN]-(manager:Manager)
    RETURN company.name AS companyName, doc.text as text, manager.managerName as asset_manager, avg(score) AS score
    ORDER BY score DESC LIMIT 50
"""
    retrieval_query_2 = """
    MATCH (doc:Document)<-[:OWNS_STOCK_IN]-(company:Company), (company)<-[:OWNS_STOCK_IN]-(manager:Manager)
    RETURN company.name AS companyName, doc.text as text, manager.managerName as asset_manager, avg(score) AS score
    ORDER BY score DESC LIMIT 50
"""

    try:
        store = Neo4jVector.from_existing_index(
            EMBEDDING_MODEL,
            url=url,
            username=username,
            password=password,
            index_name=index_name,
            retrieval_query= retrieval_query,
        )
    except:
        store = Neo4jVector.from_existing_graph(
            embedding=EMBEDDING_MODEL,
            url=url,
            username=username,
            password=password,
            index_name=index_name,
            node_label="Document",
            text_node_properties=["text"],
            embedding_node_property=node_property_name,
            retrieval_query= retrieval_query,
        )

    retriever = store.as_retriever()
    chain = RetrievalQAWithSourcesChain.from_chain_type(
        ChatOpenAI(temperature=0), chain_type="stuff", retriever=retriever
    )

    result = chain.invoke({
        "question": question},
        return_only_outputs = True
    )

    print(f'result: {result}')
    # Will return a dict with keys: answer, sources
    return result
