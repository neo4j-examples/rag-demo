import streamlit as st

import rag_vector_only
import rag_vector_graph
import rag_graph
import rag_agent
from langchain.globals import set_llm_cache
from langchain.cache import InMemoryCache
from langchain_community.callbacks import HumanApprovalCallbackHandler
from langchain_community.callbacks import StreamlitCallbackHandler

import streamlit as st
from analytics import track
from streamlit_feedback import streamlit_feedback
from rag_demo.text import title

from neo4j_semantic_layer import agent_executor as neo4j_semantic_agent
# from rag_demo.neo4j_semantic_layer import agent_executor as neo4j_semantic_agent
import logging

# Analytics tracking
if "SESSION_ID" not in st.session_state:
  track(
    "rag_demo",
    "appStarted",
    {})

set_llm_cache(InMemoryCache())

st.markdown(title, unsafe_allow_html=True)

# Define message placeholder and emoji feedback placeholder
placeholder = st.empty()
emoji_feedback = st.empty()
user_placeholder = st.empty()

# Initial images
schema_img_path = "https://res.cloudinary.com/dk0tizgdn/image/upload/v1705091904/schema_e8zkkx.png"
langchain_img_path = "https://res.cloudinary.com/dk0tizgdn/image/upload/v1704991084/langchain-neo4j_cy2mky.png"

def _approve(_input: str) -> bool:
    if _input == "echo 'Hello World'":
        return True
    msg = (
        "Do you approve of the following input"
        "Anything except 'Y'/'Yes' (case-insensitive) will be treated as a no"
    )
    msg += "\n\n" + _input + "\n"
    resp = input(msg)
    return resp.lower() in ("yes", "y")

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = [
      {"role": "ai", "content": f"This is a Proof of Concept application which shows how GenAI can be used with Neo4j to build and consume Knowledge Graphs using text data."}, 
      {"role": "ai", "content": f"""This the schema in which the EDGAR filings are stored in Neo4j: \n <img style="width: 70%; height: auto;" src="{schema_img_path}"/>"""}, 
      {"role": "ai", "content": f"""This is how the Chatbot flow goes: \n <img style="width: 70%; height: auto;" src="{langchain_img_path}"/>"""}
    ]

# RAG Options
ENABLE_VECTOR_ONLY = False
ENABLE_VECTOR_GRAPH = False
ENABLE_GRAPH_ONLY = False
ENABLE_AGENT = False
ENABLE_SIMPLE_AGENT = True

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

    # Vector only response
    with st.chat_message("ai"):
      if ENABLE_VECTOR_ONLY:
        with st.spinner('Running vector RAG...'):
          message_placeholder = st.empty()

          vector_response = rag_vector_only.get_results(user_input)
          # TODO: Update this to handle empty responses
          content = f"##### Vector only: \n" + vector_response['answer']

          # Cite sources, if any
          sources = vector_response['sources']
          sources_split = sources.split(', ')
          for source in sources_split:
            if source != "" and source != "N/A" and source != "None":
              content += f"\n - [{source}]({source})"

          track("rag_demo", "ai_response", {"type": "vector", "answer": content})
          new_message = {"role": "ai", "content": content}
          st.session_state.messages.append(new_message)

        message_placeholder.markdown(content)

      if ENABLE_VECTOR_GRAPH:
        # Vector+Graph response (styling results as separate messages)
        # with st.spinner('Running ...'):
        #   message_placeholder = st.empty()
        with st.spinner('Running Vector + Graph RAG...'):
          message_placeholder = st.empty()

          vgraph_response = rag_vector_graph.get_results(user_input)
          content = f"##### Vector + Graph: \n" + vgraph_response["answer"]

        #   # Cite sources, if any
          sources = vgraph_response['sources']
          sources_split = sources.split(', ')
          for source in sources_split:
            if source != "" and source != "N/A" and source != "None":
              content += f"\n - [{source}]({source})"

          # Cite sources, if any
          try:
            sources = vgraph_response['sources']
            sources_split = sources.split(', ')
            for source in sources_split:
              if source != "" and source != "N/A" and source != "None":
                content += f"\n - [{source}]({source})"
          except Exception as e:
            logging.error(f'Problem extracting sources: {e}')

          track("rag_demo", "ai_response", {"type": "vector_graph", "answer": content})
          new_message = {"role": "ai", "content": content}
          st.session_state.messages.append(new_message)
        
        message_placeholder.markdown(content)

      if ENABLE_GRAPH_ONLY:
        # Graph response (styling results as separate messages)
        with st.spinner('Running Graph RAG...'):
          message_placeholder = st.empty()

          vgraph_response = rag_graph.get_results(user_input)
          if vgraph_response is None:
            vgraph_response = {"result":"Could not find an answer"}

          content = f"##### Graph Only: \n" + vgraph_response["result"]

          track("rag_demo", "ai_response", {"type": "graph_only", "answer": content})
          new_message = {"role": "ai", "content": content}
          st.session_state.messages.append(new_message)

        message_placeholder.markdown(content)

      if ENABLE_AGENT:
        # Agent response
        with st.spinner('Running agent...'):
          callbacks = [HumanApprovalCallbackHandler(approve=_approve)]
          message_placeholder = st.empty()

          agent_response = neo4j_semantic_agent.invoke({"input":user_input}, callbacks=callbacks)
          print(agent_response)

          content = f"##### Agent: \n" + agent_response['output']

          track("rag_demo", "ai_response", {"type": "agent", "answer": content})
          new_message = {"role": "ai", "content": content}
          st.session_state.messages.append(new_message)

        message_placeholder.markdown(content)

      if ENABLE_SIMPLE_AGENT:
        # Agent response
        with st.spinner('Running simple agent...'):

          message_placeholder = st.empty()

          # st_callback = StreamlitCallbackHandler(st.container())

          agent_response = rag_agent.get_results(
            question=user_input
            # callbacks=[st_callback]
          )

          if isinstance(agent_response, str) is False:
            print(f'Agent response was not expected string type: {agent_response}')
          if isinstance(agent_response, dict) is True:
            print(f'Agent response was dict type: {agent_response}')

          content = f"##### Simple Agent: \n" + agent_response

          track("rag_demo", "ai_response", {"type": "simple_agent", "answer": content})
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