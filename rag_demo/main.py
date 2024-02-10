from analytics import track
from langchain.globals import set_llm_cache
from langchain.cache import InMemoryCache
from langchain_community.callbacks import HumanApprovalCallbackHandler
from langchain_community.callbacks import StreamlitCallbackHandler
from streamlit_feedback import streamlit_feedback
from rag_demo.constants import SCHEMA_IMG_PATH, LANGCHAIN_IMG_PATH, TITLE
import logging
import rag_agent
import rag_router
# import rag_multi_retriever
import streamlit as st

# Analytics tracking
if "SESSION_ID" not in st.session_state:
  track(
    "rag_demo",
    "appStarted",
    {})

# TODO: What is this for?
set_llm_cache(InMemoryCache())
llm_config = {
        "timeout": 60,
  }

# Generate app title
st.markdown(TITLE, unsafe_allow_html=True)

# Define message placeholder and emoji feedback placeholder
placeholder = st.empty()
emoji_feedback = st.empty()
user_placeholder = st.empty()

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = [
      {"role": "ai", "content": f"This is a Proof of Concept application which shows how GenAI can be used with Neo4j to build and consume Knowledge Graphs using text data."}, 
      {"role": "ai", "content": f"""This the schema in which the EDGAR filings are stored in Neo4j: \n <img style="width: 70%; height: auto;" src="{SCHEMA_IMG_PATH}"/>"""}, 
      {"role": "ai", "content": f"""This is how the Chatbot flow goes: \n <img style="width: 70%; height: auto;" src="{LANGCHAIN_IMG_PATH}"/>"""}
    ]

# Comparison Options
ENABLE_VECTOR_ONLY = False
ENABLE_VECTOR_GRAPH = False
ENABLE_GRAPH_ONLY = False
ENABLE_AGENT = True

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
      # if ENABLE_VECTOR_ONLY:
      #   with st.spinner('Running vector RAG...'):
      #     message_placeholder = st.empty()

      #     vector_response = vector_chain.get_results(user_input)
      #     # TODO: Update this to handle empty responses
      #     content = f"##### Vector only: \n" + vector_response

      #     track("rag_demo", "ai_response", {"type": "vector", "answer": content})
      #     new_message = {"role": "ai", "content": content}
      #     st.session_state.messages.append(new_message)

      #   message_placeholder.markdown(content)

      # if ENABLE_VECTOR_GRAPH:
      #   # Vector+Graph response (styling results as separate message)

      #   with st.spinner('Running Vector + Graph RAG...'):
      #     message_placeholder = st.empty()

      #     vgraph_response = vector_graph_chain.get_results(user_input)
      #     content = f"##### Vector + Graph: \n" + vgraph_response

      #   #   # Cite sources, if any
      #     # sources = vgraph_response['sources']
      #     # sources_split = sources.split(', ')
      #     # for source in sources_split:
      #     #   if source != "" and source != "N/A" and source != "None":
      #     #     content += f"\n - [{source}]({source})"

      #     # # Cite sources, if any
      #     # try:
      #     #   sources = vgraph_response['sources']
      #     #   sources_split = sources.split(', ')
      #     #   for source in sources_split:
      #     #     if source != "" and source != "N/A" and source != "None":
      #     #       content += f"\n - [{source}]({source})"
      #     # except Exception as e:
      #     #   logging.error(f'Problem extracting sources: {e}')

      #     track("rag_demo", "ai_response", {"type": "vector_graph", "answer": content})
      #     new_message = {"role": "ai", "content": content}
      #     st.session_state.messages.append(new_message)
        
      #   message_placeholder.markdown(content)

      # if ENABLE_GRAPH_ONLY:
      #   # Graph response (styling results as separate messages)
      #   with st.spinner('Running Graph RAG...'):
      #     message_placeholder = st.empty()

      #     vgraph_response = graph_chain.get_results(user_input)
      #     if vgraph_response is None:
      #       vgraph_response = {"result":"Could not find an answer"}

      #     content = f"##### Graph Only: \n" + vgraph_response["result"]

      #     track("rag_demo", "ai_response", {"type": "graph_only", "answer": content})
      #     new_message = {"role": "ai", "content": content}
      #     st.session_state.messages.append(new_message)

      #   message_placeholder.markdown(content)

      # if ENABLE_AGENT:
      # Agent response
      with st.spinner('Running agent...'):

        message_placeholder = st.empty()
        thought_container = st.container()

        # NOTE: This callback handler only works with the deprecated initialize_agent option (see rag_agent.py)
        st_callback = StreamlitCallbackHandler(
          parent_container= thought_container,
          expand_new_thoughts=False
        )
        # StreamlitCcallbackHandler api doc: https://api.python.langchain.com/en/latest/callbacks/langchain_community.callbacks.streamlit.streamlit_callback_handler.StreamlitCallbackHandler.html

        agent_response = rag_agent.get_results(
          question=user_input,
          callbacks=[st_callback]
        )

        if isinstance(agent_response, dict) is False:
          logging.warning(f'Agent response was not the expected dict type: {agent_response}')
          agent_response = str(agent_response)

        content = agent_response['output']

        # content = f"##### Simple Agent: \n" + answer

        track("rag_demo", "ai_response", {"type": "rag_agent", "answer": content})
        new_message = {"role": "ai", "content": content}
        st.session_state.messages.append(new_message)

      message_placeholder.markdown(content)

      # ROUTER OPTION
      # with st.spinner('Running router...'):

      #   message_placeholder = st.empty()
      #   thought_container = st.container()

      #   # NOTE: This callback handler only works with the deprecated initialize_agent option (see rag_agent.py)
      #   st_callback = StreamlitCallbackHandler(
      #     parent_container= thought_container,
      #     expand_new_thoughts=False
      #   )
      #   # StreamlitCcallbackHandler api doc: https://api.python.langchain.com/en/latest/callbacks/langchain_community.callbacks.streamlit.streamlit_callback_handler.StreamlitCallbackHandler.html

      #   agent_response = rag_router.get_results(
      #     question=user_input,
      #     callbacks=[st_callback]
      #   )

      #   if isinstance(agent_response, dict) is False:
      #     logging.warning(f'Agent response was not the expected dict type: {agent_response}')
      #     agent_response = str(agent_response)

      #   content = agent_response['output']

      #   # content = f"##### Simple Agent: \n" + answer

      #   track("rag_demo", "ai_response", {"type": "simple_agent", "answer": content})
      #   new_message = {"role": "ai", "content": content}
      #   st.session_state.messages.append(new_message)

      # message_placeholder.markdown(content)

      # MULTI RETRIEVER
      # with st.spinner('Running multi-retriever...'):

      #   message_placeholder = st.empty()
      #   thought_container = st.container()

      #   # NOTE: This callback handler only works with the deprecated initialize_agent option (see rag_agent.py)
      #   st_callback = StreamlitCallbackHandler(
      #     parent_container= thought_container,
      #     expand_new_thoughts=False
      #   )
      #   # StreamlitCcallbackHandler api doc: https://api.python.langchain.com/en/latest/callbacks/langchain_community.callbacks.streamlit.streamlit_callback_handler.StreamlitCallbackHandler.html

      #   agent_response = rag_multi_retriever.get_results(
      #     question=user_input,
      #     callbacks=[st_callback]
      #   )

      #   if isinstance(agent_response, dict) is False:
      #     logging.warning(f'Agent response was not the expected dict type: {agent_response}')
      #     agent_response = str(agent_response)

      #   content = agent_response['output']

      #   # content = f"##### Simple Agent: \n" + answer

      #   track("rag_demo", "ai_response", {"type": "simple_agent", "answer": content})
      #   new_message = {"role": "ai", "content": content}
      #   st.session_state.messages.append(new_message)

      # message_placeholder.markdown(content)

  emoji_feedback = st.empty()

  # Emoji feedback
with emoji_feedback.container():
  feedback = streamlit_feedback(feedback_type="thumbs")
  if feedback:
    score = feedback['score']
    last_bot_message = st.session_state['messages'][-1]['content']
    track("rag_demo", "feedback_submitted", {"score": score, "bot_message": last_bot_message})