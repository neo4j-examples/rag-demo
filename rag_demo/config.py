import streamlit as st

st.set_page_config(
    page_title="SEC EDGAR Filings",
    page_icon="🧠",
    layout="wide",
)

URI = "NEO4J_URI"
USERNAME = "NEO4J_USERNAME"
PASSWORD = "NEO4J_PASSWORD"
start_expanded = False

# Attempt to load credentials from secrets file
try: 
    s_uri = st.secrets[URI]
    s_username = st.secrets[USERNAME]
    s_password = st.secrets[PASSWORD]
except:
    s_uri = ""
    s_username = ""
    s_password = ""

# Initialize configuration into session state
if URI not in st.session_state:
    st.session_state[URI] = s_uri
if USERNAME not in st.session_state:
    st.session_state[USERNAME] = s_username 
if PASSWORD not in st.session_state:
    st.session_state[PASSWORD] = s_password

if s_uri == "" or s_username == "" or s_password == "":
    start_expanded = True

with st.expander("Config", expanded = start_expanded):
    
    # Permit overriding loaded configuration with session configuration
    uri = st.text_input(URI, value=st.session_state[URI])
    username = st.text_input(USERNAME, value=st.session_state[USERNAME])
    password = st.text_input(PASSWORD, value=st.session_state[PASSWORD],type="password")

    # Update session state with new override session configuration if present
    if uri != s_uri:
        st.session_state[URI] = uri
    if username != s_username:
        st.session_state[USERNAME] = username
    if password != s_password:
        st.session_state[PASSWORD] = password

    # If no configuration info available, don't bother processing rest of page

if st.session_state[URI] is None or st.session_state[URI] == "":
    st.info('Neo4j Credentials missing - please add above')
    st.stop()