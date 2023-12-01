import streamlit as st
import os
from dotenv import load_dotenv

st.title('Neo4j RAG Demo')
# st.write('<description TBD>')

# Sidebar for user to override or provide config options
with st.sidebar:
    st.write("SETTINGS")
    st.markdown("------------")

    # Load credentials from session state
    url = st.session_state.get("url", None)
    username = st.session_state.get("username", None)
    password = st.session_state.get("password", None)
    openai = st.session_state.get("openai", None)

    # Optionally Load credentials from .env - if present
    load_dotenv(".env")
    url = os.getenv("NEO4J_URI", "")
    username = os.getenv("NEO4J_USERNAME", "")
    password = os.getenv("NEO4J_PASSWORD", "")
    openai = os.getenv("NEO4J_PASSWORD", "")

    url = st.text_input("Neo4j URI", url)
    username = st.text_input("Neo4j Username", username)
    password = st.text_input("Neo4j Password", password)
    openai = st.text_input("OpenAI API Key", openai)

    # Update session state
    if st.button("Update Settings"):
        st.session_state["url"] = url
        st.session_state["username"] = username
        st.session_state["password"] = password
        st.session_state["openai"] = openai


# Allow users to upload multiple files
uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True)
for uploaded_file in uploaded_files:
    bytes_data = uploaded_file.read()
    st.write("filename:", uploaded_file.name)
    st.write(bytes_data)    