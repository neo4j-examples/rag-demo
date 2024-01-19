import chainlit as cl
from chainlit.input_widget import TextInput
from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.chains import RetrievalQAWithSourcesChain
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
import logging

import os
from dotenv import load_dotenv


# Initial Setup
@cl.on_chat_start
async def start():

    # Load credentials from .env - if present
    load_dotenv(".env")
    url = os.getenv("NEO4J_URI", "")
    username = os.getenv("NEO4J_USERNAME", "")
    password = os.getenv("NEO4J_PASSWORD", "")
    # openai = os.getenv("OPENAI_API_KEY", "")

    store = Neo4jVector.from_existing_index(
        OpenAIEmbeddings(),
        url=url,
        username=username,
        password=password,
        index_name="document_embeddings",
    )
    retriever = store.as_retriever()
    chain = RetrievalQAWithSourcesChain.from_chain_type(
        ChatOpenAI(temperature=0), chain_type="stuff", retriever=retriever
    )
    cl.user_session.set("chain", chain)


# When user sends a message
@cl.on_message
async def main(message: cl.Message):
    # Your custom logic goes here...

    chain = cl.user_session.get("chain")
    response = chain.invoke(message.content)
    content = response['answer']

    # Cite sources, if any
    sources = response['sources']
    sources_split = sources.split(', ')
    for source in sources_split:
        if source != "" and source != "N/A" and source != "None":
            content += f"\n - [{source}]({source})"


    # Send a response back to the user
    await cl.Message(
        content=content,
    ).send()