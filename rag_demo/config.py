import streamlit as st

# Must be first thing run by any streamlit call
st.set_page_config(
    page_title="SEC EDGAR Filings",
    page_icon="🧠",
    layout="wide",
)

# Constants
URI = "NEO4J_URI"
USERNAME = "NEO4J_USERNAME"
PASSWORD = "NEO4J_PASSWORD"
SERVICE = "SERVICE_NAME"
REGION = "REGION_NAME"
CYPHER_MODEL = "CYPHER_MODEL"
ACCESS_KEY = "ACCESS_KEY"
SECRET_KEY = "SECRET_KEY"
SEGMENT_KEY = "SEGMENT_KEY"

start_expanded = False

# Attempt to load credentials from secrets file
s_uri = st.secrets.get(URI, "")
s_username = st.secrets.get(USERNAME, "")
s_password = st.secrets.get(PASSWORD, "")
s_service = st.secrets.get(SERVICE, "")
s_region = st.secrets.get(REGION, "")
s_cypher_model = st.secrets.get(CYPHER_MODEL, "")
s_access_key = st.secrets.get(ACCESS_KEY, "")
s_secret_key = st.secrets.get(SECRET_KEY, "")
s_segment_key = st.secrets.get(SEGMENT_KEY, "")

# Initialize configuration into session state
if URI not in st.session_state:
    st.session_state[URI] = s_uri
if USERNAME not in st.session_state:
    st.session_state[USERNAME] = s_username 
if PASSWORD not in st.session_state:
    st.session_state[PASSWORD] = s_password
if SERVICE not in st.session_state:
    st.session_state[SERVICE] = s_service
if REGION not in st.session_state:
    st.session_state[REGION] = s_region
if CYPHER_MODEL not in st.session_state:
    st.session_state[CYPHER_MODEL] = s_cypher_model
if ACCESS_KEY not in st.session_state:
    st.session_state[ACCESS_KEY] = s_access_key
if SECRET_KEY not in st.session_state:
    st.session_state[SECRET_KEY] = s_secret_key
if SEGMENT_KEY not in st.session_state:
    st.session_state[SEGMENT_KEY] = s_segment_key

if s_uri == "" or s_username == "" or s_password == "":
    start_expanded = True

with st.expander("Config", expanded = start_expanded):
    
    # TextFields permiting overriding loaded configuration with session configuration
    uri = st.text_input(URI, value=st.session_state[URI])
    username = st.text_input(USERNAME, value=st.session_state[USERNAME])
    password = st.text_input(PASSWORD, value=st.session_state[PASSWORD],type="password")
    service = st.text_input(SERVICE, value=st.session_state[SERVICE])
    region = st.text_input(REGION, value=st.session_state[REGION])
    cypher_model = st.text_input(CYPHER_MODEL, value=st.session_state[CYPHER_MODEL])
    access_key = st.text_input("AWS ACCESS_KEY", value=st.session_state[ACCESS_KEY])
    secret_key = st.text_input("AWS SECRET_KEY", value=st.session_state[SECRET_KEY],type="password")
    segment_key = st.text_input("SEGMENT_KEY", value=st.session_state[SEGMENT_KEY])

    # Update session state with new override session configuration if present
    if uri != s_uri:
        st.session_state[URI] = uri
    if username != s_username:
        st.session_state[USERNAME] = username
    if password != s_password:
        st.session_state[PASSWORD] = password
    if service != s_service:
        st.session_state[SERVICE] = service
    if region != s_region:
        st.session_state[REGION] = region
    if cypher_model != s_cypher_model:
        st.session_state[CYPHER_MODEL] = cypher_model
    if access_key != s_access_key:
        st.session_state[ACCESS_KEY] = access_key
    if secret_key != s_secret_key:
        st.session_state[SECRET_KEY] = secret_key
    if segment_key != s_segment_key:
        st.session_state[SEGMENT_KEY] = segment_key

# If no configuration info available, don't bother processing rest of page
# TODO: Expand on this
if st.session_state[URI] is None or st.session_state[URI] == "":
    st.info('Neo4j Credentials missing - please add above')
    st.stop()