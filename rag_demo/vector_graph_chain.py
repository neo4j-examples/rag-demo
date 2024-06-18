from langchain.prompts.prompt import PromptTemplate

from langchain_community.vectorstores import Neo4jVector
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from retry import retry
import logging
import streamlit as st

VECTOR_GRAPH_PROMPT_TEMPLATE = """Task: Provide names and related information financial filing data strictly based on the text and instructions provided.
Instructions:
1. Answer the question STRICTLY based on the text.
2. Do not assume or retrieve any information outside of the text provided.
3. Use as much information from the text as possible, including sources and links if available.
4. If the output is empty, just respond None.

Question:
{question}
"""
VECTOR_GRAPH_PROMPT = PromptTemplate(
    input_variables=["question"], template=VECTOR_GRAPH_PROMPT_TEMPLATE
)

if "USER_OPENAI_API_KEY" in st.session_state:
    openai_key = st.session_state["USER_OPENAI_API_KEY"]
else:
    openai_key = st.secrets["OPENAI_API_KEY"]

EMBEDDING_MODEL = OpenAIEmbeddings(openai_api_key=openai_key)
MEMORY = ConversationBufferMemory(
    memory_key="chat_history",
    input_key="question",
    output_key="answer",
    return_messages=True,
)

index_name = "form_10k_chunks"
node_property_name = "textEmbedding"
url = st.secrets["NEO4J_URI"]
username = st.secrets["NEO4J_USERNAME"]
password = st.secrets["NEO4J_PASSWORD"]
retrieval_query = """
    WITH node AS doc, score as similarity
    ORDER BY similarity DESC LIMIT 5
    CALL { WITH doc
        OPTIONAL MATCH (prevDoc:Chunk)-[:NEXT]->(doc)
        OPTIONAL MATCH (doc)-[:NEXT]->(nextDoc:Chunk)
        RETURN prevDoc, doc AS result, nextDoc
    }
    WITH result, prevDoc, nextDoc, similarity
    CALL {
        WITH result
        OPTIONAL MATCH (result)-[:PART_OF]->(:Form)<-[:FILED]-(company:Company)
        OPTIONAL MATCH (company)<-[:OWNS_STOCK_IN]-(manager:Manager)
        WITH result, company.name as companyName, apoc.text.join(collect(manager.managerName),';') as managers
        WHERE companyName IS NOT NULL OR managers > ""
        WITH result, companyName, managers
        ORDER BY result.score DESC
        RETURN result as document, result.score as popularity, companyName, managers
    }
    RETURN coalesce(prevDoc.text,'') + coalesce(document.text,'') + coalesce(nextDoc.text,'') + '\n Company: ' + coalesce(companyName,'') + '\n Managers: ' + coalesce(managers,'') as text, 
        similarity as score,
        {companies: coalesce(companyName,''), managers: coalesce(managers,''), source: document.source} AS metadata
"""


vector_store = None
try:
    logging.debug(f"Attempting to retrieve existing vector index: {index_name}...")
    vector_store = Neo4jVector.from_existing_index(
        embedding=EMBEDDING_MODEL,
        url=url,
        username=username,
        password=password,
        index_name=index_name,
        embedding_node_property=node_property_name,
        retrieval_query=retrieval_query,
    )
    logging.debug(f"Using existing index: {index_name}")
except:
    logging.debug(
        f"No existing index found. Attempting to create a new vector index named {index_name}..."
    )
    try:
        vector_store = Neo4jVector.from_existing_graph(
            embedding=EMBEDDING_MODEL,
            url=url,
            username=username,
            password=password,
            index_name=index_name,
            node_label="Chunk",
            text_node_properties=["text"],
            embedding_node_property=node_property_name,
            retrieval_query=retrieval_query,
        )
        logging.debug(f"Created new index: {index_name}")
    except Exception as e:
        logging.error(f"Failed to retrieve existing or to create a Neo4jVector: {e}")

if vector_store is None:
    logging.error(f"Failed to retrieve or create a Neo4jVector. Exiting.")
    exit()

vector_graph_retriever = vector_store.as_retriever()

vector_graph_chain = RetrievalQAWithSourcesChain.from_chain_type(
    ChatOpenAI(temperature=0, openai_api_key=openai_key),
    chain_type="stuff",
    retriever=vector_graph_retriever,
    memory=MEMORY,
    reduce_k_below_max_tokens=True,
    max_tokens_limit=3000,
)


@retry(tries=2, delay=5)
def get_results(question) -> str:
    """Generate response using Neo4jVector using vector index only

    Args:
        question (str): User query

    Returns:
        str: Formatted string answer with citations, if available.
    """

    logging.info(f"Using Neo4j url: {url}")

    prompt = VECTOR_GRAPH_PROMPT.format(question=question)

    # Returns a dict with keys: answer, sources
    chain_result = vector_graph_chain.invoke(
        {"question": question},
        prompt=prompt,
        return_only_outputs=True,
    )

    logging.debug(f"chain_result: {chain_result}")
    result = chain_result["answer"]

    # Cite sources, if any
    sources = chain_result["sources"]
    sources_split = sources.split(", ")
    for source in sources_split:
        if source != "" and source != "N/A" and source != "None":
            result += f"\n - [{source}]({source})"

    return result
