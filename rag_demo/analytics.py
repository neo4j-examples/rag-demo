from segment import analytics
import streamlit as st
import uuid

SESSION_ID = "SESSION_ID"

try:
    analytics.write_key = st.secrets["SEGMENT_WRITE_KEY"]
    ANALYTICS_ENABLED = True
except:
    ANALYTICS_ENABLED = False

def track(
        user_id: str, 
        event_name: str, 
        properties: dict):
    """Simple wrapper for Segment's analytics.track()

    Args:
        user_id (str): Unique identifier for session/user
        event_name (str): Name of tracking event
        properties (dict): Any optional additional properties
    """

    if ANALYTICS_ENABLED is False:
        return
    
    if SESSION_ID not in st.session_state:
        st.session_state[SESSION_ID] = str(uuid.uuid4())

    properties["session_id"] = st.session_state[SESSION_ID]

    analytics.track(
        user_id = user_id, 
        event = event_name, 
        properties =  properties)