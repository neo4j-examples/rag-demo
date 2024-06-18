from json import loads, dumps
from langchain.prompts.prompt import PromptTemplate

from langchain_community.vectorstores import Neo4jVector
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from retry import retry
import logging
import streamlit as st

VECTOR_PROMPT_TEMPLATE = """Human: You are a Financial expert with SEC filings who can answer questions only based on the context below.
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
VECTOR_PROMPT = PromptTemplate(
    input_variables=["input", "context"], template=VECTOR_PROMPT_TEMPLATE
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
node_property_name = "textopenaiembedding"
url = st.secrets["NEO4J_URI"]
username = st.secrets["NEO4J_USERNAME"]
password = st.secrets["NEO4J_PASSWORD"]


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
        )
        logging.debug(f"Created new index: {index_name}")
    except Exception as e:
        logging.error(f"Failed to retrieve existing or to create a Neo4jVector: {e}")

if vector_store is None:
    logging.error(f"Failed to retrieve or create a Neo4jVector. Exiting.")
    exit()

vector_retriever = vector_store.as_retriever()

vector_chain = RetrievalQAWithSourcesChain.from_chain_type(
    ChatOpenAI(temperature=0, openai_api_key=openai_key),
    chain_type="stuff",
    retriever=vector_retriever,
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

    # Returns a dict with keys: answer, sources
    chain_result = vector_chain.invoke(
        {"question": question},
        prompt=VECTOR_PROMPT,
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


# Using the vector store directly. But this could blow out the token count
# @retry(tries=5, delay=5)
# def get_results(question)-> str:
#     """Generate response using Neo4jVector using vector index only

#     Args:
#         question (str): User query

#     Returns:
#         str: Formatted string answer with citations, if available.
#     """

#     logging.info(f'Using Neo4j url: {url}')

#     # Returns a dict with keys: answer, sources
#     vector_result = vector_store.similarity_search(question, k=3)

#     logging.debug(f'chain_result: {vector_result}')

#     result = vector_result

#     return result
