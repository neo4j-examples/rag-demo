from langchain.document_loaders.image import UnstructuredImageLoader
from langchain.document_loaders import ImageCaptionLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.embeddings.openai import OpenAIEmbeddings
import tempfile
import logging
from n4j_utils import add_chunk, chunk_exists, add_chunks, add_document_and_chunk_connections, add_tags_to_chunk, document_exists, add_document, add_tags_to_document
import os
from tag_generator import get_tags

# UnstructuredImageLoader
# Required packages not in docs 
# unstructured
# pdf2image
# pikepdf

#ImageCaptionLoader undocumented requirements:
#pytorch
#chromadb

# Image -> text 
def upload(file: any):

    url = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    if document_exists(
        url=url,
        username=username,
        password =password,
        filename=file.name
    ) is True:
        logging.info(f'File {file} already uploaded')
        return False
    

    # API doc for ImageCaptionLoader: https://api.python.langchain.com/en/stable/document_loaders/langchain.document_loaders.image_captions.ImageCaptionLoader.html?highlight=imagecaptionloader#langchain.document_loaders.image_captions.ImageCaptionLoader
    loader = ImageCaptionLoader(file.read())

    index = VectorstoreIndexCreator().from_loaders([loader])
    result = index.query("What's this image about?")
    logging.info(f'image uploader query result: {result}')

    add_document(
        file.name,
        result,
        url,
        username,
        password
    )

    tags = get_tags(result)
    add_tags_to_document(
        file.name,
        tags,
        url,
        username,
        password
    )
    
    return True