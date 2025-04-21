import streamlit as st
from retry import retry
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
from graph_cypher_tool import graph_cypher_tool  # Make sure this is defined correctly

# Choose one of the LLMs
# llm = Ollama(model="llama3")
llm = ChatOpenAI(
    openai_api_key=st.secrets["OPENAI_API_KEY"],
    temperature=0.2,
    model_name="gpt-4o-mini"
)

# Conversation history
conversation_history = []

def process_with_llm(question: str) -> str:
    """Uses LLM to respond based on prior messages and graph result."""

    # 1. Build past conversation text
    conversation_text = "\n".join([
        f"User: {msg['input']}\nBot: {msg['output']}"
        for msg in conversation_history
    ])

    # 2. Run the question through the Cypher tool
    tool_output = graph_cypher_tool.invoke(question)
    result_only = tool_output.get("result", "No results found.")

    # 3. LLM prompt with only the result
    final_prompt = f"""
Based on the conversation and the user question, provide a relevant and helpful response.

Conversation:
{conversation_text}

Current question: {question}

Here is the output from the database:
{result_only}

Please process the output and answer the user question clearly. If the output is not empty please add [[button_query]] in last answer.
    """.strip()

    final_response = llm.predict(final_prompt).strip()

    # 4. Inject Neo4j button if there was a result
    if tool_output.get("result"):
        last_query = tool_output.get("intermediate_steps", [{}])[-1].get("query", "")
        final_response = final_response.replace(
            "[[button_query]]",
            f"[Open Neo4J](http://localhost:7474/browser/?cmd=edit&arg={last_query})"
        )
    else:
        final_response = final_response.replace("[[button_query]]", "")

    # 5. Update history
    conversation_history.append({
        "input": question,
        "output": final_response
    })

    return final_response

@retry(tries=2, delay=10)
def get_results(question: str) -> dict:
    """Main processing function for external calls"""
    llm_processed_output = process_with_llm(question=question)
    return {
        "input": question,
        "output": llm_processed_output,
    }


