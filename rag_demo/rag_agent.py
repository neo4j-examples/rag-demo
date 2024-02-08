from langchain.agents import load_tools, AgentType
from langchain.agents import initialize_agent 
from langchain import hub # requires langchainhub package
from langchain_community.llms import OpenAI
from retry import retry
from langchain.prompts.prompt import PromptTemplate
from rag_demo.neo4j_semantic_layer.graph_tool import graph_cypher
from rag_demo.neo4j_semantic_layer.vector_tool import vector_graph
from langchain.agents import AgentExecutor, create_react_agent


llm = OpenAI(temperature=0, streaming=True)
# llm-math requires numexpr package
tools = load_tools(["llm-math"], llm=llm)
tools = tools + [graph_cypher, vector_graph]

# Using new agent executor - Streamlit handler doesn't seem to work with this option
# prompt = hub.pull("hwchase17/react")

# agent = create_react_agent(llm, tools, prompt)

# agent_executor = AgentExecutor(
#     agent=agent,
#     tools=tools,
#     verbose=True,
#     return_intermediate_steps = True,
#     max_iterations=6,
#     early_stopping_method = "generate"
# )

# @retry(tries=2, delay=12)
# def get_results(question, callbacks):
#     # Streamlit callbacks work with the old agent run, but not the new agent_executor
#     # response = agent.run(question, callbacks=callbacks)
#     response = agent_executor.invoke({"input": question}, callbacks=callbacks)
#     return response

# Older agent method
agent = initialize_agent(
    tools, 
    llm, 
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
    verbose=True
)

agent.agent.llm_chain.prompt.template

@retry(tries=3, delay=8)
def get_results(question, callbacks = []):
    result = agent.run(question, callbacks=callbacks)
    return result