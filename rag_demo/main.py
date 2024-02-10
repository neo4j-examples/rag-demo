from analytics import track
from langchain.globals import set_llm_cache
from langchain.cache import InMemoryCache
from langchain_community.callbacks import HumanApprovalCallbackHandler
from langchain_community.callbacks import StreamlitCallbackHandler
from streamlit_feedback import streamlit_feedback
from constants import SCHEMA_IMG_PATH, LANGCHAIN_IMG_PATH, TITLE
import logging
import rag_agent
import streamlit as st

# Anonymous Session Analytics
if "SESSION_ID" not in st.session_state:
  track(
    "rag_demo",
    "appStarted",
    {})

# LangChain caching to reduce API calls
set_llm_cache(InMemoryCache())

# App title
st.markdown(TITLE, unsafe_allow_html=True)

# Define message placeholder and emoji feedback placeholder
placeholder = st.empty()
emoji_feedback = st.empty()
user_placeholder = st.empty()

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = [
      {"role": "ai", "content": f"This is a Proof of Concept application which shows how GenAI can be used with Neo4j to build and consume Knowledge Graphs using both vectors and structured data."}, 
      {"role": "ai", "content": f"""This the schema in which the EDGAR filings are stored in Neo4j: \n <img style="width: 70%; height: auto;" src="{SCHEMA_IMG_PATH}"/>"""}, 
      {"role": "ai", "content": f"""This is how the Chatbot flow goes: \n <img style="width: 70%; height: auto;" src="{LANGCHAIN_IMG_PATH}"/>"""}
    ]

# Display chat messages from history on app rerun
with placeholder.container():
  for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# User input placeholder
if user_input := st.chat_input(placeholder="Ask question on the SEC Filings", key="user_input"):
  with user_placeholder.container():
    track("rag_demo", "question_submitted", {"question": user_input})
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
      st.markdown(user_input)

    with st.chat_message("ai"):

      # Agent response
      with st.spinner('...'):

        message_placeholder = st.empty()
        thought_container = st.container()

        # For displaying chain of thought - this callback handler appears to only works with the deprecated initialize_agent option (see rag_agent.py)
        # st_callback = StreamlitCallbackHandler(
        #   parent_container= thought_container,
        #   expand_new_thoughts=False
        # )
        # StreamlitCcallbackHandler api doc: https://api.python.langchain.com/en/latest/callbacks/langchain_community.callbacks.streamlit.streamlit_callback_handler.StreamlitCallbackHandler.html

        agent_response = rag_agent.get_results(
          question=user_input,
          callbacks=[]
        )

        if isinstance(agent_response, dict) is False:
          logging.warning(f'Agent response was not the expected dict type: {agent_response}')
          agent_response = str(agent_response)

        content = agent_response['output']

        track("rag_demo", "ai_response", {"type": "rag_agent", "answer": content})
        new_message = {"role": "ai", "content": content}
        st.session_state.messages.append(new_message)

      message_placeholder.markdown(content)

  emoji_feedback = st.empty()

# Emoji feedback
with emoji_feedback.container():
  feedback = streamlit_feedback(feedback_type="thumbs")
  if feedback:
    score = feedback['score']
    last_bot_message = st.session_state['messages'][-1]['content']
    track("rag_demo", "feedback_submitted", {"score": score, "bot_message": last_bot_message})