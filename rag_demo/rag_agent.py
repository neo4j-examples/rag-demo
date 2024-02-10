from langchain.agents import load_tools, AgentType, initialize_agent, create_openai_tools_agent,AgentExecutor, create_react_agent
from langchain import hub # requires langchainhub package
# from langchain_community.llms import OpenAI
from langchain_openai import OpenAI
from langchain_experimental.plan_and_execute import PlanAndExecute, load_agent_executor, load_chat_planner
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts.prompt import PromptTemplate
from rag_demo.tools.graph_tool import graph_tool
from rag_demo.tools.vector_tool import vector_tool
from retry import retry


llm = OpenAI(temperature=0)
tools = load_tools([], llm=llm)
tools = tools + [graph_tool, vector_tool]

# OLDER AGENT - Will be deprecated in future, but works with the Streamlit callback handler
# agent_executor = initialize_agent(
#     tools, 
#     llm, 
#     agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
#     verbose=True
# )

# agent_executor.agent.llm_chain.prompt.template

# EXPERIMENTAL PLANNER
# This goes through a very verbose chain of thought
# model = ChatOpenAI(model="gpt-4",temperature=0)
# planner = load_chat_planner(model)
# planner.llm_chain.prompt.messages[0].content
# executor = load_agent_executor(model, tools, verbose=True)
# agent_executor = PlanAndExecute(planner=planner, executor=executor, verbose=True)

# OPENAI TOOLS AGENT EXECUTOR
# Requires model that can make use of additional parameters
# prompt = hub.pull("hwchase17/openai-tools-agent")
# agent = create_openai_tools_agent(llm, tools, prompt)
# agent_executor = AgentExecutor(
#     agent=agent, 
#     tools=tools, 
#     verbose=True)

# REACT AGENT EXECUTOR - Streamlit handler doesn't seem to work with this option

# 🤷 Where does this actually pull from? 
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

@retry(tries=2, delay=12)
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