import streamlit as st
import os
from dotenv import load_dotenv

def add_sidebar():
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
        if url is None: url = os.getenv("NEO4J_URI", "")
        if username is None: username = os.getenv("NEO4J_USER", "")
        if password is None: password = os.getenv("NEO4J_PASSWORD", "")
        if openai is None: openai = os.getenv("NEO4J_PASSWORD", "")

        # Allow users to override credentials
        url = st.text_input("Neo4j URI", url, help="See the [Neo4j Getting Started Guide](https://neo4j.com/docs/getting-started/get-started-with-neo4j/#neo4j-first-steps) to create a Neo4j database.")
        username = st.text_input("Neo4j Username", username)
        password = st.text_input("Neo4j Password", password, type="password")
        openai = st.text_input("OpenAI API Key", openai, type="password", help="Find or create an OpenAI API Key from your [User Settings](https://beta.openai.com/account/api-keys)")

        # Update session state
        if st.button("Update Settings"):
            st.session_state["url"] = url
            st.session_state["username"] = username
            st.session_state["password"] = password
            st.session_state["openai"] = openai