from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import io
import logging
import os
from n4j_utils import add_chunks, add_document_and_chunk_connections, add_tags_to_chunk, document_exists
from tag_generator import get_tags

def upload(file: any) -> bool:

    url = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    if document_exists(
        url,
        username,
        password,
        file.name
    ) is True:
        logging.debug(f'file {file} already uploaded')
        return False

    open_pdf_file = io.BytesIO(file.read()) 
    pdf_reader = PdfReader(open_pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, length_function=len
        )
    chunks = text_splitter.split_text(text=text)
    embeddings = OpenAIEmbeddings()

    logging.info(f'pdf chunks length: {len(chunks)}')
    logging.info(f'pdf chunks: {chunks}')

    Neo4jVector.from_texts(
        chunks,
        url=url,
        username=username,
        password=password,
        embedding=embeddings,
        index_name="pdf_index",
        node_label="Chunk",
        pre_delete_collection=False,  # Delete existing PDF data
    )

    add_document_and_chunk_connections(
        filename=file.name,
        full_text = "",
        chunks = chunks,
        url=url,
        username=username,
        password = password
    )

    for c in chunks:
        tags = get_tags(c)
        add_tags_to_chunk(
            c,
            tags,
            url,
            username,
            password
        )

    return True