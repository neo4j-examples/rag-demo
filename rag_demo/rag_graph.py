from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain.prompts.prompt import PromptTemplate
import streamlit as st

from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from services import llm, embedding_model

PROMPT_TEMPLATE ="""
You are answering questions about SEC filings from the information provided in the <context> section below.
Always respond with information from the <context> section.
Do not add data from external sources.
If you are not sure about an answer, still state the information and say that you are unsure.

<question>
{question}
</question>

Here is the context:
<context>
{context}
</context>

Assistant:

"""
PROMPT = PromptTemplate(
    input_variables=["question","context"], template=PROMPT_TEMPLATE
)

CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
Examples: Here are a few examples of generated Cypher statements for particular questions:
# How many Managers own Companies?
MATCH (m:Manager)-[:OWNS_STOCK_IN]->(c:Company)
RETURN count(DISTINCT m)

# Which companies are in healthcare
MATCH (c:Company)-[:IN]->(i:Industry) 
WHERE toLower(i.industry) contains 'health' 
RETURN c.name

# Which companies are vulnerable to lithium shortage?
MATCH (co:Company)-[fi]-(f:Form)-[po]-(c:Chunk)
WHERE c.text CONTAINS "lithium"
RETURN DISTINCT count(c) as chunks, co.name ORDER BY chunks desc

The question is:
{question}"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)


EMBEDDING_MODEL = embedding_model # OpenAIEmbeddings()
MEMORY = ConversationBufferMemory(memory_key="chat_history", input_key='question', output_key='answer', return_messages=True)

url = st.secrets["NEO4J_URI"]
username = st.secrets["NEO4J_USERNAME"]
password = st.secrets["NEO4J_PASSWORD"]
openai_key = st.secrets["OPENAI_API_KEY"]

graph = Neo4jGraph(
    url=url,
    username=username,
    password=password,
    sanitize = True
)
# TEMP
llm_key = st.secrets["OPENAI_API_KEY"]

# @retry(tries=1, delay=30)
def get_results(question):

    print(f'rag_graph: Using Neo4j creds: ur: {url}, username: {username}, password: {password}')

    graph.refresh_schema()

    chain = GraphCypherQAChain.from_llm(
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
        graph=graph,
        verbose=True, 
        return_intermediate_steps = True,
        return_direct = True
    )

    result = chain.invoke({
        "query": question},
        prompt=CYPHER_GENERATION_PROMPT,
        return_only_outputs = True,
    )

    print(f'result: {result}')
    # Will return a dict with keys: answer, sources
    return result