from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain.prompts.prompt import PromptTemplate
from langchain.llms.bedrock import Bedrock
from retry import retry
from timeit import default_timer as timer
import streamlit as st

from neo4j_driver import run_query
from json import loads, dumps
from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains.conversation.memory import ConversationBufferMemory

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
xPROMPT_TEMPLATE = """Human: You are a Financial expert with SEC filings who can answer questions only based on the context below.
* Answer the question STRICTLY based on the context provided in JSON below.
* Do not assume or retrieve any information outside of the context 
* Use three sentences maximum and keep the answer concise
* Think step by step before answering.
* Do not return helpful or extra text or apologies
* Just return summary to the user. DO NOT start with Here is a summary
* List the results in rich text format if there are more than one results
* If the context is empty, just respond None

<question>
{question}
</question>

Here is the context:
<context>
{context}
</context>

Assistant:"""
PROMPT = PromptTemplate(
    input_variables=["question","context"], template=PROMPT_TEMPLATE
)

EMBEDDING_MODEL = embedding_model # OpenAIEmbeddings()
MEMORY = ConversationBufferMemory(memory_key="chat_history", input_key='question', output_key='answer', return_messages=True)

url = st.secrets["NEO4J_URI"]
username = st.secrets["NEO4J_USERNAME"]
password = st.secrets["NEO4J_PASSWORD"]

# graph = Neo4jGraph(
#     url=url,
#     username=username,
#     password=password,
#     sanitize = True
# )
# TEMP
llm_key = st.secrets["OPENAI_API_KEY"]

# @retry(tries=1, delay=30)
def get_results(question):

    # TODO: Update index and node property names to reflect the embedding origin LLM,
    # ie "document_text_openai" index and "text_openai_embedding"
    # Currently the try-except block below only works with small datasets, it needs to be replaced 
    # with a large node count variation

    index_name = "form_10k_chunks"
    node_property_name = "textopenaiembedding"
    url=st.secrets["NEO4J_URI"]
    username=st.secrets["NEO4J_USERNAME"]
    password=st.secrets["NEO4J_PASSWORD"]
    retrieval_query = """
    WITH node AS doc, score as similarity
    ORDER BY similarity DESC LIMIT 3
    CALL { WITH doc
        OPTIONAL MATCH (prevDoc:Chunk)-[:NEXT]->(doc)
        OPTIONAL MATCH (doc)-[:NEXT]->(nextDoc:Chunk)
        RETURN prevDoc, doc AS result, nextDoc
    }
    WITH result, prevDoc, nextDoc, similarity
    CALL {
        WITH result
        OPTIONAL MATCH (result)-[:PART_OF]->(:Form)<-[:FILED]-(company:Company), (company)<-[:OWNS_STOCK_IN]-(manager:Manager)
        WITH result, company.name as companyName, apoc.text.join(collect(manager.managerName),';') as managers
        WHERE companyName IS NOT NULL OR managers > ""
        WITH result, companyName, managers
        ORDER BY result.score DESC
        RETURN result as document, result.score as popularity, companyName, managers LIMIT 3
    }
    RETURN coalesce(prevDoc.text,'') + coalesce(document.text,'') + coalesce(nextDoc.text,'') as text, similarity as score, 
        {documentId: coalesce(document.chunkId,''), company: coalesce(companyName,''), managers: coalesce(managers,''), source: document.source} AS metadata LIMIT 3
"""
# retrieval_query = """
#     WITH node AS doc, score as similarity
#     CALL { WITH doc
#         OPTIONAL MATCH (prevDoc:Document)-[:NEXT]->(doc)
#         OPTIONAL MATCH (doc)-[:NEXT]->(nextDoc:Document)
#         RETURN prevDoc, doc AS result, nextDoc
#     }
#     WITH result, prevDoc, nextDoc, similarity
#     CALL {
#         WITH result
#         OPTIONAL MATCH (result)<-[:HAS_CHUNK]-(:Form)-[:FILED]->(company:Company), (company)<-[:OWNS_STOCK_IN]-(manager:Manager)
#         WITH result, company.name as companyName, apoc.text.join(collect(manager.managerName),';') as managers
#         WHERE companyName IS NOT NULL OR managers > ""
#         WITH result, companyName, managers
#         ORDER BY result.score DESC
#         RETURN result as document, result.score as popularity, companyName, managers
#     }
#     RETURN '##DocumentID: ' + coalesce(document.documentId,'') +'\n'+ 
#         '##Text: ' + coalesce(prevDoc.text+'\n','') + coalesce(document.text+'\n','') + coalesce(nextDoc.text+'\n','') +
#         '###Company: ' + coalesce(companyName,'') +'\n'+ '###Managers: ' + coalesce(managers,'') as text, 
#         similarity as score, {source: document.source} AS metadata
#     ORDER BY similarity ASC // so that best answers are the last
# """

    print(f'rag_vector_graph: Using Neo4j creds: ur: {url}, username: {username}, password: {password}')

    try:
        store = Neo4jVector.from_existing_index(
            embedding=EMBEDDING_MODEL,
            url=url,
            username=username,
            password=password,
            index_name=index_name,
            embedding_node_property=node_property_name,
            retrieval_query=retrieval_query,
        )
    except:
        store = Neo4jVector.from_existing_graph(
            embedding=EMBEDDING_MODEL,
            url=url,
            username=username,
            password=password,
            index_name=index_name,
            node_label="Chunk",
            text_node_properties=["text"],
            embedding_node_property=node_property_name,
            # retrieval_query=retrieval_query,
        )

    retriever = store.as_retriever()

    context = retriever.get_relevant_documents(question)
    print(f'Context: {context}')
    completePrompt = PROMPT.format(question=question, context=context)
    # print(f'CompletePrompt: {completePrompt}')
    # chat_llm = ChatOpenAI(openai_api_key=llm_key)
    # result = chat_llm.invoke(completePrompt)

    chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm, 
        chain_type="stuff", 
        retriever=retriever,
        memory=MEMORY,
        max_tokens_limit=2000
    )

    result = chain.invoke({
        "question": question},
        prompt=completePrompt,
        return_only_outputs = True,
    )

    print(f'result: {result}')
    # Will return a dict with keys: answer, sources
    return result
