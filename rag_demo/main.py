from analytics import track
from free_use_manager import (
    free_questions_exhausted,
    user_supplied_openai_key_unavailable,
    decrement_free_questions,
)
from langchain.globals import set_llm_cache
from langchain_community.cache import InMemoryCache
from streamlit_feedback import streamlit_feedback
from constants import TITLE
import logging
#import rag_agent
import  graph_cypher_chain
from graph_cypher_tool import GrpahCypherTool
import streamlit as st
from sidebar import sidebar

# Logging options
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Anonymous Session Analytics
if "SESSION_ID" not in st.session_state:
    # Track method will create and add session id to state on first run
    track("rag_demo", "appStarted", {})

# LangChain caching to reduce API calls
set_llm_cache(InMemoryCache())

# App title
st.markdown(TITLE, unsafe_allow_html=True)
sidebar()

# Define message placeholder and emoji feedback placeholder
placeholder = st.empty()
emoji_feedback = st.empty()
user_placeholder = st.empty()
cypher_tool=GrpahCypherTool()
   
# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "ai",
            "content": f"This is a Proof of Concept application which shows how GenAI can be used with Neo4j to build and consume Knowledge Graphs using both vectors and structured data.\nSee the sidebar for more information!",
        },
        # {"role": "ai", "content": f"""This the schema in which the EDGAR filings are stored in Neo4j: \n <img style="width: 70%; height: auto;" src="{SCHEMA_IMG_PATH}"/>"""},
        # {"role": "ai", "content": f"""This is how the Chatbot flow goes: \n <img style="width: 70%; height: auto;" src="{LANGCHAIN_IMG_PATH}"/>"""}
    ]

# Display chat messages from history on app rerun
with placeholder.container():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

# User input - switch between sidebar sample quick select or actual user input. Clunky but works.
print("before free_questions_exhausted",free_questions_exhausted(), user_supplied_openai_key_unavailable() )

if free_questions_exhausted() and user_supplied_openai_key_unavailable():
    st.warning(
        "Thank you for trying out the Auto Civil Engineer. Please input your OpenAI Key in the sidebar to continue asking questions."
    )
    st.stop()
print("after free_questions_exhausted")
if "sample" in st.session_state and st.session_state["sample"] is not None:
    user_input = st.session_state["sample"]
else:
    user_input = st.chat_input(
        placeholder="Ask question on the IFC project", key="user_input"
    )

if user_input:
    with user_placeholder.container():
        track("rag_demo", "question_submitted", {"question": user_input})
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("ai"):

            # Agent response
            with st.spinner("..."):

                message_placeholder = st.empty()
                thought_container = st.container()

                # For displaying chain of thought - this callback handler appears to only works with the deprecated initialize_agent option (see rag_agent.py)
                # st_callback = StreamlitCallbackHandler(
                #   parent_container= thought_container,
                #   expand_new_thoughts=False
                # )
                # StreamlitCcallbackHandler api doc: https://api.python.langchain.com/en/latest/callbacks/langchain_community.callbacks.streamlit.streamlit_callback_handler.StreamlitCallbackHandler.html

#                agent_response = rag_agent.get_results(
#                    question=user_input, callbacks=[]
#                )
#                agent_response = graph_cypher_chain.get_results(
#                    question=user_input
#                )    
                agent_response=cypher_tool.run(tool_input=user_input)            
                if isinstance(agent_response, dict) is False:
                    logging.warning(
                        f"Agent response was not the expected dict type: {agent_response}"
                    )
                    agent_response = str(agent_response)
                content = str(agent_response)
 #               content = agent_response["output"]

                track(
                    "rag_demo", "ai_response", {"type": "rag_agent", "answer": content}
                )
                new_message = {"role": "ai", "content": content}
                st.session_state.messages.append(new_message)

                decrement_free_questions()

            message_placeholder.markdown(content)

    # Reinsert user chat input if sample quick select was previously used.
    if "sample" in st.session_state and st.session_state["sample"] is not None:
        st.session_state["sample"] = None
        user_input = st.chat_input(
            placeholder="Ask question on the SEC Filings", key="user_input"
        )

    emoji_feedback = st.empty()

# Emoji feedback
with emoji_feedback.container():
    feedback = streamlit_feedback(feedback_type="thumbs")
    if feedback:
        score = feedback["score"]
        last_bot_message = st.session_state["messages"][-1]["content"]
        track(
            "rag_demo",
            "feedback_submitted",
            {"score": score, "bot_message": last_bot_message},
        )
