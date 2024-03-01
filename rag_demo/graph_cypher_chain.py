from langchain.chains import GraphCypherQAChain
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain_community.graphs import Neo4jGraph
from langchain.prompts.prompt import PromptTemplate
from langchain_openai import ChatOpenAI
from retry import retry
import logging
import streamlit as st

CYPHER_GENERATION_TEMPLATE = """Task: Generate Cypher statement to query a graph database strictly based on the schema and instructions provided.
Instructions:
1. Use only nodes, relationships, and properties mentioned in the schema.
2. Always enclose the Cypher output inside 3 backticks. Do not add 'cypher' after the backticks.
3. Always do a case-insensitive and fuzzy search for any properties related search. Eg: to search for a Company name use `toLower(c.name) contains 'neo4j'`
4. Always use aliases to refer the node in the query
5. Always return count(DISTINCT n) for aggregations to avoid duplicates
6. `OWNS_STOCK_IN` relationship is syonymous with `OWNS` and `OWNER`
7. Use examples of questions and accurate Cypher statements below to guide you.

Schema:
{schema}

Examples: Here are a few examples of generated Cypher statements for particular questions:

# How many Managers own Companies?
MATCH (m:Manager)-[:OWNS_STOCK_IN]->(c:Company)
RETURN count(DISTINCT m)

# How many companies are in filings?
MATCH (c:Company) 
RETURN count(DISTINCT c)

# Which companies are vulnerable to material shortage?
MATCH (co:Company)-[fi]-(f:Form)-[po]-(c:Chunk)
WHERE toLower(c.text) CONTAINS "material"
RETURN DISTINCT count(c) as chunks, co.name ORDER BY chunks desc

# Which companies are in a specific industry?
MATCH (co:Company)-[fi]-(f:Form)-[po]-(c:Chunk)
WHERE toLower(c.text) CONTAINS "industryName"
RETURN DISTINCT count(c) as chunks, co.name ORDER BY chunks desc

The question is:
{question}"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)

MEMORY = ConversationBufferMemory(
    memory_key="chat_history", 
    input_key='question', 
    output_key='answer', 
    return_messages=True)

url = st.secrets["NEO4J_URI"]
username = st.secrets["NEO4J_USERNAME"]
password = st.secrets["NEO4J_PASSWORD"]
openai_key = st.secrets["OPENAI_API_KEY"]
llm_key = st.secrets["OPENAI_API_KEY"]

graph = Neo4jGraph(
    url=url,
    username=username,
    password=password,
    sanitize = True
)

# Official API doc for GraphCypherQAChain at: https://api.python.langchain.com/en/latest/chains/langchain.chains.graph_qa.base.GraphQAChain.html#
graph_chain = GraphCypherQAChain.from_llm(
    cypher_llm=ChatOpenAI(
        openai_api_key=openai_key, 
        temperature=0, 
        model_name="gpt-4"
    ),
    qa_llm=ChatOpenAI(
        openai_api_key=openai_key, 
        temperature=0, 
        model_name="gpt-4"
    ),
    validate_cypher= True,
    graph=graph,
    verbose=True, 
    # return_intermediate_steps = True,
    return_direct = True
)

@retry(tries=2, delay=12)
def get_results(question) -> str:
    """Generate a response from a GraphCypherQAChain targeted at generating answered related to relationships. 

    Args:
        question (str): User query

    Returns:
        str: Answer from chain
    """

    logging.info(f'Using Neo4j database at url: {url}')

    graph.refresh_schema()

    prompt=CYPHER_GENERATION_PROMPT.format(schema=graph.get_schema, question=question)
    print('Prompt:', prompt)

    chain_result = None

    try:
        chain_result = graph_chain.invoke({
            "query": question},
            prompt=prompt,
            return_only_outputs = True,
        )
    except Exception as e:
        # Occurs when the chain can not generate a cypher statement
        # for the question with the given database schema
        logging.warning(f'Handled exception running graphCypher chain: {e}')

    logging.debug(f'chain_result: {chain_result}')

    if chain_result is None:
        return "Sorry, I couldn't find an answer to your question"
    
    result = chain_result.get("result", None)

    return result