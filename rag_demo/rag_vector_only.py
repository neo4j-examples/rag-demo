from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain.prompts.prompt import PromptTemplate
from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.chains import RetrievalQAWithSourcesChain
# from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferMemory
from retry import retry
from timeit import default_timer as timer
import streamlit as st
from neo4j_driver import run_query
from json import loads, dumps
    
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

EMBEDDING_MODEL = embedding_model #OpenAIEmbeddings()
MEMORY = ConversationBufferMemory(memory_key="chat_history", input_key='question', output_key='answer', return_messages=True)

def df_to_context(df):
    result = df.to_json(orient="records")
    parsed = loads(result)
    return dumps(parsed)

@retry(tries=5, delay=5)
def get_results(question):

    index_name = "form_10k_chunks"
    node_property_name = "textopenaiembedding"
    url=st.secrets["NEO4J_URI"]
    username=st.secrets["NEO4J_USERNAME"]
    password=st.secrets["NEO4J_PASSWORD"]  

    print(f'rag_vector_only: Using Neo4j creds: ur: {url}, username: {username}, password: {password}')

    store = None
    try:
        print(f'Attempting to retrieve existing vector index: {index_name}...')
        store = Neo4jVector.from_existing_index(
            embedding=EMBEDDING_MODEL,
            url=url,
            username=username,
            password=password,
            index_name=index_name,
            embedding_node_property=node_property_name,
        )
        print(f'Using existing index: {index_name}')
    except:
        print(f'No existing index found. Attempting to create a new vector index named {index_name}...')
        try:
            store = Neo4jVector.from_existing_graph(
                embedding=EMBEDDING_MODEL,
                url=url,
                username=username,
                password=password,
                index_name=index_name,
                node_label="Chunk",
                text_node_properties=["text"],
                embedding_node_property=node_property_name,
            )
            print(f'Created new index: {index_name}')
        except Exception as e:
            print(f'Failed to create Neo4jVector: {e}')
            return None

    retriever = store.as_retriever()

    chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm, # ChatOpenAI(temperature=0), 
        chain_type="stuff", 
        retriever=retriever,
        memory=MEMORY
    )

    result = chain.invoke({
        "question": question},
        prompt=PROMPT,
        return_only_outputs = True
    )

    print(f'result: {result}')
    # Will return a dict with keys: answer, sources
    return result


