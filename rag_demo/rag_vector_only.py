from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferMemory
from retry import retry
import streamlit as st
from json import loads, dumps

from rag import generate_chain

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
{question}
</question>

Here is the context:
<context>
{context}
</context>

Assistant:"""
PROMPT = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

EMBEDDING_MODEL = OpenAIEmbeddings()
MEMORY = ConversationBufferMemory(memory_key="chat_history", input_key='question', output_key='answer',
                                  return_messages=True)


def df_to_context(df):
    result = df.to_json(orient="records")
    parsed = loads(result)
    return dumps(parsed)


@retry(tries=5, delay=5)
def get_results(question):
    index_name = "form_10k_chunks"
    node_property_name = "textEmbedding"
    url = st.secrets["NEO4J_URI"]
    username = st.secrets["NEO4J_USERNAME"]
    password = st.secrets["NEO4J_PASSWORD"]

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
    chat_llm = ChatOpenAI(temperature=0)
    chain = generate_chain(retriever, chat_llm, PROMPT)

    result = chain.invoke({"question": question})

    print(f'result: {result}')
    return result
