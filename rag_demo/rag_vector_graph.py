from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain.prompts.prompt import PromptTemplate
from langchain.llms.bedrock import Bedrock
from retry import retry
from timeit import default_timer as timer
import streamlit as st

from neo4j_driver import run_query
from json import loads, dumps
from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains.conversation.memory import ConversationBufferMemory

from services import llm, embedding_model

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

EMBEDDING_MODEL = embedding_model # OpenAIEmbeddings()
MEMORY = ConversationBufferMemory(memory_key="chat_history", input_key='question', output_key='answer', return_messages=True)

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

    # TODO: Update index and node property names to reflect the embedding origin LLM,
    # ie "document_text_openai" index and "text_openai_embedding"
    # Currently the try-except block below only works with small datasets, it needs to be replaced 
    # with a large node count variation

    index_name = "form_10k_chunks"
    node_property_name = "textEmbedding"
    url=st.secrets["NEO4J_URI"]
    username=st.secrets["NEO4J_USERNAME"]
    password=st.secrets["NEO4J_PASSWORD"]
    retrieval_query = """
    WITH node AS doc, score as similarity
    CALL { with doc
        OPTIONAL MATCH (doc)<-[:HAS_CHUNK]-(:Form)-[:FILED]->(company:Company), (company)<-[:OWNS_STOCK_IN]-(manager:Manager)
        WITH doc, company.name as companyName, apoc.text.join(collect(manager.managerName),';') as managers
        ORDER BY doc.score DESC
        RETURN doc as document, companyName, managers
    } 
    RETURN '##Document: ' + coalesce(document.documentId,'') +'\n'+ coalesce(document.text+'\n','') + 
        '###Company: ' + coalesce(companyName,'') +'\n'+ '###Managers: ' + coalesce(managers,'') as text, 
        similarity as score, {source: document.source} AS metadata
    ORDER BY similarity ASC // so that best answers are the last
"""
#     retrieval_query = """
#     WITH node AS doc, score as similarity
#     CALL { with doc
#         OPTIONAL MATCH (doc)<-[:HAS_CHUNK]-(:Form)-[:FILED]->(company:Company), (company)<-[:OWNS_STOCK_IN]-(manager:Manager)
#         WITH doc, company.name as companyName, collect(manager.managerName) as managers
#         ORDER BY doc.score DESC
#         RETURN doc as document, companyName, reduce(str='', manager IN managers | str + manager + '; ') as managersList
#     } 
#     RETURN coalesce('##Document: ' + document.documentId + '\n' + document.text + '\n### Company: ' + companyName + '\n### Managers: ' + managersList) as text, 
#         similarity as score, {source: document.source} AS metadata
#     ORDER BY similarity ASC // so that best answers are the last
# """


    try:
        store = Neo4jVector.from_existing_index(
            embedding=EMBEDDING_MODEL,
            url=url,
            username=username,
            password=password,
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
        llm, 
        chain_type="stuff", 
        retriever=retriever,
        memory=MEMORY
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
