from langchain.prompts.prompt import PromptTemplate
from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from retry import retry
import logging
import streamlit as st

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

EMBEDDING_MODEL = OpenAIEmbeddings()
MEMORY = ConversationBufferMemory(memory_key="chat_history", input_key='question', output_key='answer', return_messages=True)

@retry(tries=1, delay=15)
def get_results(question):
    """Generates a response using Neo4jVector with a Retrieval Cypher Query
    """

    # TODO: Update index and node property names to reflect the embedding origin LLM,
    # ie "document_text_openai" index and "text_openai_embedding"
    # Currently the try-except block below only works with small datasets, it needs to be replaced 
    # with a large node count variation

    index_name = "form_10k_chunks"
    node_property_name = "textopenaiembedding"
    url = st.secrets["NEO4J_URI"]
    username = st.secrets["NEO4J_USERNAME"]
    password = st.secrets["NEO4J_PASSWORD"]
    openai_key = st.secrets["OPENAI_API_KEY"]

    # Additional details on how to best create a retrieval_query: https://neo4j.com/developer-blog/neo4j-langchain-vector-index-implementation/
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

    logging.info(f'Using Neo4j database url: {url}')

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
            retrieval_query=retrieval_query,
        )

    retriever = store.as_retriever()

    context = retriever.get_relevant_documents(question)
    logging.debug(f'Context: {context}')
    completePrompt = PROMPT.format(question=question, context=context)
    # logging.debug(f'CompletePrompt: {completePrompt}')
    # chat_llm = ChatOpenAI(openai_api_key=llm_key)
    # result = chat_llm.invoke(completePrompt)

    chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm = ChatOpenAI(
            openai_api_key=openai_key, 
            temperature=0, 
            model_name="gpt-4"
        ), 
        chain_type="stuff", 
        retriever=retriever,
        memory=MEMORY,
        max_tokens_limit=2000
    )

    # Returns a dict with keys: answer, sources
    chain_result = chain.invoke({
        "question": question},
        prompt=completePrompt,
        return_only_outputs = True,
    )

    logging.debug(f'chain_result: {chain_result}')

    result = chain_result['answer']

    # Cite sources, if any
    sources = chain_result['sources']
    sources_split = sources.split(', ')
    for source in sources_split:
        if source != "" and source != "N/A" and source != "None":
            result += f"\n - [{source}]({source})"

    return result