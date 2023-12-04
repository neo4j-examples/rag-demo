import streamlit as st
from app_streamlit_sidebar import add_sidebar
from uploaders.langchain_pdf import upload as load_pdf
from uploaders.langchain_txt import upload as load_txt
from utilities import enable_logging
import logging

def main():
    st.title('Neo4j RAG Demo')

    # Setup Neo4j driver and standard logging
    enable_logging()

    # Sidebar for user to override or provide config options
    add_sidebar()

    # Allow users to upload multiple files
    files = st.file_uploader("Upload files", accept_multiple_files=True)

    # TODO: Dedupe. There is known bug in Streamlit where the same file will be tracked multiple times on. https://github.com/streamlit/streamlit/issues/4877

    for file in files:
        bytes_data = file.read()
        logging.debug(f"File loaded: {file.__dict__}")
        if file.type == "application/pdf":
            load_pdf(bytes_data)
        elif file.type == "text/plain":
            load_txt(bytes_data)
        else:
            st.error(f"File type {file.type} not supported")

    # TODO: Add Chat interface

if __name__ == "__main__":
    main()