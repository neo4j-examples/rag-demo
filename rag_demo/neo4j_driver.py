import os
from graphdatascience import GraphDataScience

import streamlit as st

host = st.session_state.get("NEO4J_URI", "")
user = st.session_state.get("NEO4J_USERNAME", "")
password = st.session_state.get("NEO4J_PASSWORD", "")

gds = GraphDataScience(
    host,
    auth=(user, password),
    aura_ds=True)

gds.set_database("neo4j")

def run_query(query, params = {}):
    return gds.run_cypher(query, params)
