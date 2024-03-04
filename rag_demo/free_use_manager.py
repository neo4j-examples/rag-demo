# Manages number of free questions permitted before forcing user to supply their own OpenAI Key

import streamlit as st

def free_questions_exhausted()-> bool:
    if "FREE_QUESTIONS_REMAINING" not in st.session_state:
        st.session_state["FREE_QUESTIONS_REMAINING"] = st.secrets["FREE_QUESTIONS_PER_SESSION"]
    
    remaining = st.session_state["FREE_QUESTIONS_REMAINING"]
    return remaining <= 0

def user_supplied_openai_key_unavailable()-> bool:
    if "USER_OPENAI_KEY" not in st.session_state:
        return True
    uok = st.session_state["USER_OPENAI_KEY"]
    if uok is None or uok == "":
        return True
    return False

def decrement_free_questions():
    if "FREE_QUESTIONS_REMAINING" not in st.session_state:
        st.session_state["FREE_QUESTIONS_REMAINING"] = st.secrets["FREE_QUESTIONS_PER_SESSION"]
    remaining = st.session_state["FREE_QUESTIONS_REMAINING"]
    if remaining > 0:
        st.session_state["FREE_QUESTIONS_REMAINING"] = remaining - 1