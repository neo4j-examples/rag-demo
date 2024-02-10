from langchain.agents import load_tools, AgentExecutor, create_react_agent
from langchain import hub # requires langchainhub package
from langchain_openai import OpenAI
from graph_tool import graph_tool
from vector_tool import vector_tool
from retry import retry

# Setup tools the agent will use
llm = OpenAI(temperature=0)
tools = load_tools([], llm=llm)
tools = tools + [graph_tool, vector_tool]


# REACT AGENT EXECUTOR

prompt = hub.pull("hwchase17/react")

# More on agent types: https://python.langchain.com/docs/modules/agents/agent_types/
agent = create_react_agent(llm, tools, prompt)

# NOTE: early_stopping_method generate option ONLY available for multi-action agents
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    return_intermediate_steps = True,
    max_iterations=6,
    # early_stopping_method = "generate"
)

@retry(tries=2, delay=6)
def get_results(question, callbacks) -> dict:
    """Starts a LangChain agent to generate an answer using one of several Neo4j RAG tools.

    Args:
        question (str): User query
        callbacks (list): List of optional LangChain callback handlers

    Returns:
        dict: Final answer as a dict with the keys: input, output, intermediate_steps
    """

    response = agent_executor.invoke({"input": question}, callbacks=callbacks)
    return response