import streamlit as st
import streamlit.components.v1 as components
from streamlit_chat import message
from app_streamlit_sidebar import add_sidebar
from upload import upload, type_supported
from utilities import enable_logging
import logging
import os

def on_input_change():
    user_input = st.session_state.user_input
    st.session_state.past.append(user_input)
    st.session_state.generated.append("The messages from Bot\nWith new line")

def on_btn_click():
    del st.session_state.past[:]
    del st.session_state.generated[:]

def main():

    # if "UPLOADED_FILES" not in st.session_state:
    #     st.session_state["UPLOADED_FILES"] = []
    st.set_page_config(layout="wide")
    st.title('Neo4j RAG Demo')

    # Setup Neo4j driver and standard logging
    enable_logging()

    # Sidebar for user to override or provide config options
    add_sidebar()

    # FILE UPLOADS
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

    # CHAT INTERFACE
    # st.session_state.setdefault(
    #     'past', 
    #     []
    # )
    # st.session_state.setdefault(
    #     'generated', 
    #     [{'type': 'normal', 'data': 'Please upload some data to get started'}]
    # )
    # chat_placeholder = st.empty()
    # with chat_placeholder.container():    
    #     for i in range(len(st.session_state['generated'])):                
    #         # message(st.session_state['past'][i], is_user=True, key=f"{i}_user")
    #         message(
    #             st.session_state['generated'][i]['data'], 
    #             key=f"{i}", 
    #             allow_html=True,
    #             is_table=True if st.session_state['generated'][i]['type']=='table' else False
    #         )

    #     st.button("Clear message", on_click=on_btn_click)

    # with st.container():
    #     st.text_input("User Input:", on_change=on_input_change, key="user_input")

    # Show graph
    # url = os.getenv("NEO4J_URI")
    # username = os.getenv("NEO4J_USER")
    # password = os.getenv("NEO4J_PASSWORD")

    # components.iframe(f"https://neodash.graphapp.io/", height=800)
    # placeholder = st.empty()

    # with placeholder.container():
    #     st.markdown("""
    #         <style>
    #             iframe {
    #                 position: fixed;
    #                 background: #000;
    #                 border: none;
    #                 top: 10; right: 0;
    #                 bottom: 0; left: 0;
    #                 width: 100%;
    #                 height: 100%;
    #             }
    #         </style>
    #         <iframe 
    #             src="https://workspace-preview.neo4j.io/workspace/explore" 
    #             frameborder="10" style="overflow:hidden;height:92%;width:100%" 
    #             height="100%" width="100%" title="Bloom">
    #         </iframe>
    #     """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()