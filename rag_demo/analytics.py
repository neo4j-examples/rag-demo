from segment import analytics
import streamlit as st
import logging
import uuid

SESSION_ID = "SESSION_ID"

analytics.write_key = st.secrets["SEGMENT_WRITE_KEY"]

def track(
        user_id: str, 
        event_name: str, 
        properties: dict):

    if SESSION_ID not in st.session_state:
        st.session_state[SESSION_ID] = str(uuid.uuid4())

    properties["session_id"] = st.session_state[SESSION_ID]

    analytics.track(
        user_id = user_id, 
        event = event_name, 
        properties =  properties)