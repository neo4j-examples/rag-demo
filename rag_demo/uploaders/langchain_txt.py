from langchain.docstore.document import Document
from langchain.document_loaders import TextLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Neo4jVector
import os
import logging

async def upload(file: any):
    """
    Uploads a text file to a Neo4j database.

    Args:
        neo4j_credits: Tuple containing the hostname, username, and password of the target Neo4j instance

        nodes: A dictionary of objects to upload. Each key is a unique node label and contains a list of records as dictionary objects.
    
    Raises:
        Exceptions if data is not in the correct format or if the upload fails.
    """
    # loader = TextLoader(file)
    # documents = loader.load()
    # text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    # docs = text_splitter.split_documents(documents)

    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    docs = [Document(page_content=x) for x in text_splitter.split_text(file.decode())]
    embeddings = OpenAIEmbeddings()

    url = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    logging.info(f'Neo4j credentials found: {url}, {username}, {password}')

    db = Neo4jVector.from_documents(
        docs, 
        embeddings, 
        url=url, 
        username=username, 
        password=password)

    query = "What is this document about?"
    docs = db.similarity_search(query)

    logging.info(docs[0].page_content)
    # TODO: Validate data was uploaded?