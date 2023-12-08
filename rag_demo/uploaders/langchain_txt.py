from langchain.docstore.document import Document
from langchain.document_loaders import TextLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Neo4jVector
from langchain.graphs import Neo4jGraph
import os
import logging
from neo4j.exceptions import ClientError
from tag_generator import get_tags
from n4j_utils import add_chunks, add_tags_to_chunk, add_document_and_chunk_connections,document_exists

def upload(
        file: any) -> bool:
    """
    Uploads a text file to a Neo4j database.

    Args:
        neo4j_credits: Tuple containing the hostname, username, and password of the target Neo4j instance

        nodes: A dictionary of objects to upload. Each key is a unique node label and contains a list of records as dictionary objects.
    
    Raises:
        Exceptions if data is not in the correct format or if the upload fails.
    """
    url = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    try:
        content = file.read()
    except Exception as _:
        try:
            content = file.content
        except Exception as e:
            logging.error(f'Could not read file {file}')

    if document_exists(
        url=url,
        username=username,
        password=password,
        filename = file.name
        ) is True:
        return False
    
    text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=100)
    docs = [Document(page_content=x) for x in text_splitter.split_text(content.decode())]
    embeddings = OpenAIEmbeddings()

    add_chunks(
        docs,
        embeddings,
        url,
        username,
        password
    )

    add_document_and_chunk_connections(
        file.name,
        content,
        [d.page_content for d in docs],
        url,
        username,
        password
    )

    for doc in docs:
        tags = get_tags(doc.page_content)
        add_tags_to_chunk(
            doc.page_content,
            tags,
            url,
            username,
            password
        )

    return True

# def upload(
#         file: any):
#     """
#     Uploads a text file to a Neo4j database.

#     Args:
#         neo4j_credits: Tuple containing the hostname, username, and password of the target Neo4j instance

#         nodes: A dictionary of objects to upload. Each key is a unique node label and contains a list of records as dictionary objects.
    
#     Raises:
#         Exceptions if data is not in the correct format or if the upload fails.
#     """
#     url = os.getenv("NEO4J_URI")
#     username = os.getenv("NEO4J_USER")
#     password = os.getenv("NEO4J_PASSWORD")
#     content = file.read()

#     text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=100)
#     docs = [Document(page_content=x) for x in text_splitter.split_text(content.decode())]
#     embeddings = OpenAIEmbeddings()

#     for doc in docs:
#         if document_exists(
#             url=url,
#             username=username,
#             password=password,
#             filename = file.name,
#             text = doc.page_content) is True:
#             continue

#         # Add documents and embeddings to Neo4j
#         db = Neo4jVector.from_documents(
#             [doc], 
#             embeddings, 
#             url=url, 
#             username=username, 
#             password=password)

#         # Connect original document with chunks
#         # Upload document as a node and connect all the chunks to it
#         # TODO: Add data for parent doc (time, etc)
#         graph = Neo4jGraph(
#             url=url,
#             username=username,
#             password=password
#         )
#         query = """
#                 MERGE (doc:Document {name:$filename})
#                 WITH doc
#                 UNWIND $children AS child
#                 MATCH (c:Chunk {text:child})
#                 MERGE (c)-[:CHILD_OF]->(doc)
#                 """
#         params = {
#             "filename": file.name,
#             "children": [d.page_content for d in docs]
#         }
#         try:
#             graph.query(
#                 query,
#                 params
#             )
#         except ClientError:
#             pass
        
#         # Extract Tags
#         tags = get_tags(doc.page_content)
#         # tags = [x.strip() for x in tags_str.split(",")]
#         graph = Neo4jGraph(
#             url=url,
#             username=username,
#             password=password
#         )
#         query = """
#                 MATCH (c:Chunk {text:$text})
#                 WITH c
#                 UNWIND $tags AS tag
#                 MERGE (t:Tag {name:tag})
#                 MERGE (c)-[:TAGGED]->(t)
#                 """
#         params = {
#             "text": doc.page_content,
#             "tags": tags
#         }
#         try:
#             graph.query(
#                 query,
#                 params
#             )
#         except ClientError:
#             pass
