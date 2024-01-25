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


PROMPT_TEMPLATE = """Human: You are a Financial expert with SEC filings who can answer questions only based on the context below.
* Answer the question STRICTLY based on the context provided in JSON below.
* Do not assume or retrieve any information outside of the context 
* Use three sentences maximum and keep the answer concise
* Think step by step before answering.
* Do not return helpful or extra text or apologies
* Just return summary to the user. DO NOT start with Here is a summary
* List the results in rich text format if there are more than one results
* If the context is empty, just respond None

<question>
{input}
</question>

Here is the context:
<context>
{context}
</context>

Assistant:"""
PROMPT = PromptTemplate(
    input_variables=["input","context"], template=PROMPT_TEMPLATE
)

EMBEDDING_MODEL = OpenAIEmbeddings()

url = st.secrets["NEO4J_URI"]
username = st.secrets["NEO4J_USERNAME"]
password = st.secrets["NEO4J_PASSWORD"]

graph = Neo4jGraph(
    url=url,
    username=username,
    password=password,
    # sanitize = True
)

def df_to_context(df):
    result = df.to_json(orient="records")
    parsed = loads(result)
    return dumps(parsed)


@retry(tries=5, delay=5)
def get_results(question):

    index_name = "form_10k_chunks"
    node_property_name = "textEmbedding"
    url=st.secrets["NEO4J_URI"]
    username=st.secrets["NEO4J_USERNAME"]
    password=st.secrets["NEO4J_PASSWORD"]
    retrieval_query = """
    WITH node AS doc, score as similarity
    CALL { with doc
        OPTIONAL MATCH (doc)<-[:HAS_CHUNK]-(:Form)-[:FILED]->(company:Company), (company)<-[:OWNS_STOCK_IN]-(manager:Manager)
        WITH doc, company.name as companyName, collect(manager.managerName) as managers
        ORDER BY doc.score DESC
        LIMIT 5
        RETURN doc as document, companyName, managers
    } 
    RETURN '##Document: ' + document.documentId + '\n' + document.text + '\n' 
        + companyName + '\n' + managers as text, similarity as score, {source: document.source} AS metadata
    ORDER BY similarity ASC // so that best answers are the last
"""
#     retrieval_query = f"""
#     WITH node AS doc, score
#     OPTIONAL MATCH (doc)<-[:HAS_CHUNK]-(:Form)-[:FILED]->(company:Company), (company)<-[:OWNS_STOCK_IN]-(manager:Manager)
#     WITH doc, score, company.name as companyName, collect(manager.managerName) as managers
#     RETURN doc.text AS text, score, {{companyName: companyName, assetManager: managers, popularityScore: doc.score, source: doc.source}} as metadata
#     ORDER BY score DESC LIMIT 5
# """

    try:
        store = Neo4jVector.from_existing_index(
            embedding=EMBEDDING_MODEL,
            url=url,
            username=username,
            password=password,
            database="neo4j",
            index_name=index_name,
            embedding_node_property=node_property_name,
            retrieval_query=retrieval_query,
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
            retrieval_query=retrieval_query,
        )

    retriever = store.as_retriever()

    chain = RetrievalQAWithSourcesChain.from_chain_type(
        ChatOpenAI(temperature=0), chain_type="stuff", retriever=retriever
    )

    # print(question)
    # print(PROMPT)
    # TODO: We're not stuffing the prompt with the context documents.
    # Should we send the prompt separately? or put the question into it and send that instead?

    result = chain.invoke({
        "question": question},
        prompt=PROMPT,
        return_only_outputs = True,
    )

    print(f'result: {result}')
    # Will return a dict with keys: answer, sources
    return result
