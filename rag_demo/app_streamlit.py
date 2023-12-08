import streamlit as st
from app_streamlit_sidebar import add_sidebar
from upload import upload, type_supported
from utilities import enable_logging
import logging



def main():

    # if "UPLOADED_FILES" not in st.session_state:
    #     st.session_state["UPLOADED_FILES"] = []

    st.title('Neo4j RAG Demo')

    # Setup Neo4j driver and standard logging
    enable_logging()

    # Sidebar for user to override or provide config options
    add_sidebar()

    # Allow users to upload multiple files
    files = st.file_uploader("Upload files", accept_multiple_files=True)
    for file in files:
        
        # Dedupe. There is known bug in Streamlit where the same file will be tracked multiple times on. https://github.com/streamlit/streamlit/issues/4877
        # if file.name in st.session_state["UPLOADED_FILES"]:
        #     logging.debug(f'file {file.name} already uploaded. Skipping...')
        #     continue

        if type_supported(file.type) == False:
            st.error(f'File type {file.type} for {file.name} not supported')
            continue

        success = upload(file)

        if success is False:
            st.error(f"Problem uploading or file with same filename already uploaded")
            continue
    
        # st.session_state["UPLOADED_FILES"].append(file.name)
        st.success(f'File(s) uploaded')

    # TODO: Add Chat interface

if __name__ == "__main__":
    main()