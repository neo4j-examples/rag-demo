import streamlit as st
# from streamlit_chat import message
import streamlit.components.v1 as components
from streamlit.components.v1 import html

import rag_vector_only
import rag_vector_graph
from timeit import default_timer as timer
from PIL import Image
from langchain.globals import set_llm_cache
from langchain.cache import InMemoryCache

from analytics import track
from streamlit_feedback import streamlit_feedback

# Analytics tracking
track(
   "rag_demo",
   "appStarted",
   {})

set_llm_cache(InMemoryCache())

st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto&display=swap');
    </style>
    <div style='text-align: center; font-size: 2.5rem; font-weight: 600; font-family: "Roboto"; color: #018BFF; line-height:1; '>SEC EDGAR Filings</div>
    <div style='text-align: center; font-size: 1.5rem; font-weight: 300; font-family: "Roboto"; color: rgb(179 185 182); line-height:0; '>
        Powered by <svg width="80" height="60" xmlns="http://www.w3.org/2000/svg" id="Layer_1" data-name="Layer 1" viewBox="0 0 200 75"><path d="M39.23,19c-10.58,0-17.68,6.16-17.68,18.11v8.52A8,8,0,0,1,25,44.81a7.89,7.89,0,0,1,3.46.8V37.07c0-7.75,4.28-11.73,10.8-11.73S50,29.32,50,37.07V55.69h6.89V37.07C56.91,25.05,49.81,19,39.23,19Z"/><path d="M60.66,37.8c0-10.87,8-18.84,19.27-18.84s19.13,8,19.13,18.84v2.53H67.9c1,6.38,5.8,9.93,12,9.93,4.64,0,7.9-1.45,10-4.56h7.6c-2.75,6.66-9.27,10.94-17.6,10.94C68.63,56.64,60.66,48.67,60.66,37.8Zm31.15-3.62c-1.38-5.73-6.08-8.84-11.88-8.84S69.5,28.53,68.12,34.18Z"/><path d="M102.74,37.8c0-10.86,8-18.83,19.27-18.83s19.27,8,19.27,18.83-8,18.84-19.27,18.84S102.74,48.67,102.74,37.8Zm31.59,0c0-7.24-4.93-12.46-12.32-12.46S109.7,30.56,109.7,37.8,114.62,50.26,122,50.26,134.33,45.05,134.33,37.8Z"/><path d="M180.64,62.82h.8c4.42,0,6.08-2,6.08-7V20.16h6.89v35.2c0,8.84-3.48,13.4-12.32,13.4h-1.45Z"/><path d="M177.2,59.14h-6.89V50.65H152.86A8.64,8.64,0,0,1,145,46.2a7.72,7.72,0,0,1,.94-8.16L161.6,17.49a8.65,8.65,0,0,1,15.6,5.13V44.54h5.17v6.11H177.2ZM151.67,41.8a1.76,1.76,0,0,0-.32,1,1.72,1.72,0,0,0,1.73,1.73h17.23V22.45a1.7,1.7,0,0,0-1.19-1.68,2.36,2.36,0,0,0-.63-.09,1.63,1.63,0,0,0-1.36.73L151.67,41.8Z"/><path d="M191,5.53a5.9,5.9,0,1,0,5.89,5.9A5.9,5.9,0,0,0,191,5.53Z" fill="#018bff"/><path d="M24.7,47a5.84,5.84,0,0,0-3.54,1.2l-6.48-4.43a6,6,0,0,0,.22-1.59A5.89,5.89,0,1,0,9,48a5.81,5.81,0,0,0,3.54-1.2L19,51.26a5.89,5.89,0,0,0,0,3.19l-6.48,4.43A5.81,5.81,0,0,0,9,57.68a5.9,5.9,0,1,0,5.89,5.89A6,6,0,0,0,14.68,62l6.48-4.43a5.84,5.84,0,0,0,3.54,1.2A5.9,5.9,0,0,0,24.7,47Z" fill="#018bff"/></svg>
           
    </div>
""", unsafe_allow_html=True)

# Define message placeholder and emoji feedback placeholder
placeholder = st.empty()
emoji_feedback = st.empty()
user_placeholder = st.empty()

# Initial images
schema_img_path = "https://res.cloudinary.com/dk0tizgdn/image/upload/v1705091904/schema_e8zkkx.png"
langchain_img_path = "https://res.cloudinary.com/dk0tizgdn/image/upload/v1704991084/langchain-neo4j_cy2mky.png"

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = [
      {"role": "ai", "content": f"This is a Proof of Concept application which shows how GenAI can be used with Neo4j to build and consume Knowledge Graphs using text data."}, 
      {"role": "ai", "content": f"""This the schema in which the EDGAR filings are stored in Neo4j: \n <img style="width: 70%; height: auto;" src="{schema_img_path}"/>"""}, 
      {"role": "ai", "content": f"""This is how the Chatbot flow goes: \n <img style="width: 70%; height: auto;" src="{langchain_img_path}"/>"""}
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
      with st.spinner('Running ...'):
        message_placeholder = st.empty()

        # Vector only response
        vector_response = rag_vector_only.get_results(user_input)
        content = f"##### Vector only: \n" + vector_response['answer']

        # Cite sources, if any
        sources = vector_response['sources']
        sources_split = sources.split(', ')
        for source in sources_split:
          if source != "" and source != "N/A" and source != "None":
            content += f"\n - [{source}]({source})"

        new_message = {"role": "ai", "content": content}
        st.session_state.messages.append(new_message)

      message_placeholder.markdown(content)

      # Vector+Graph response (styling results as separate messages)
      with st.spinner('Running ...'):
        message_placeholder = st.empty()

        vgraph_response = rag_vector_graph.get_results(user_input)
        content = f"##### Vector + Graph: \n" + vgraph_response['answer']

        # Cite sources, if any
        sources = vgraph_response['sources']
        sources_split = sources.split(', ')
        for source in sources_split:
          if source != "" and source != "N/A" and source != "None":
            content += f"\n - [{source}]({source})"

        new_message = {"role": "ai", "content": content}
        st.session_state.messages.append(new_message)

      message_placeholder.markdown(content)

      # # Alternative: style results as single combined response message
      # vector_response = rag_vector_graph.get_results(user_input)
      # content += f"\n ##### Vector + Graph: \n" + vector_response['answer']

      # # Cite sources, if any
      # sources = vector_response['sources']
      # sources_split = sources.split(', ')
      # for source in sources_split:
      #   if source != "" and source != "N/A" and source != "None":
      #     content += f"\n - [{source}]({source})"

      # new_message = {"role": "ai", "content": content}
      # st.session_state.messages.append(new_message)

      # message_placeholder.markdown(content)
    
  emoji_feedback = st.empty()

  # Emoji feedback
with emoji_feedback.container():
  feedback = streamlit_feedback(feedback_type="thumbs")
  if feedback:
    score = feedback['score']
    last_bot_message = st.session_state['messages'][-1]['content']
    track("rag_demo", "feedback_submitted", {"score": score, "bot_message": last_bot_message})