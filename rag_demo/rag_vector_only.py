from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain.prompts.prompt import PromptTemplate
from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.chains import RetrievalQAWithSourcesChain
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from retry import retry
from timeit import default_timer as timer
import streamlit as st
from neo4j_driver import run_query
from json import loads, dumps
    

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

    try:
        store = Neo4jVector.from_existing_index(
            embedding=EMBEDDING_MODEL,
            url=url,
            username=username,
            password=password,
            index_name=index_name,
            embedding_node_property=node_property_name,
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
        )

    retriever = store.as_retriever()
    # retriever.get_relevant_documents(question)[0]

    chain = RetrievalQAWithSourcesChain.from_chain_type(
        ChatOpenAI(temperature=0), chain_type="stuff", retriever=retriever
    )

    result = chain.invoke({
        "question": question},
        prompt=PROMPT,
        return_only_outputs = True
    )

    print(f'result: {result}')
    # Will return a dict with keys: answer, sources
    return result


