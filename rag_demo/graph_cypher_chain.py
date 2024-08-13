from langchain.chains import GraphCypherQAChain
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain_community.graphs import Neo4jGraph
from langchain.prompts.prompt import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from retry import retry
import logging
import streamlit as st

CYPHER_GENERATION_TEMPLATE = """Task: Generate Cypher statement to query a graph database strictly based on the schema and instructions provided.
Instructions:
1. Use only nodes, relationships, and properties mentioned in the schema. dont invent anything.
2. Always enclose the Cypher output inside 3 backticks. Do not add anythin except for the 'cypher' after the backticks. 
3. Always do a case-insensitive and fuzzy search for any properties related search. Eg: to search for a Company name use `toLower(c.name) contains 'neo4j'`
4. Always use aliases to refer the node in the query
5. Always return count(DISTINCT n) for aggregations to avoid duplicates
6. All the data is based on ifc (industry foundation classes) standard.
7. Use examples of questions and accurate Cypher statements below to guide you.
8. Do not include any explanations or apologies in your responses.


Schema:
{schema}

Examples: Here are a few examples of generated Cypher statements for particular questions:
###########################################################################################
# Get gross volume of all entities that have gross volume (such as IfcBeam, IfcWallStandardCase, IfcSlab, IfcColumn):
MATCH (n:IfcQuantityVolume)<-[:Quantities]-(:IfcElementQuantity)<-[:RelatingPropertyDefinition]-(:IfcRelDefinesByProperties)-[:RelatedObjects]->(o)
RETURN LABELS(o)[0] AS entity_name, o.ObjectType AS entity_type, n.VolumeValue AS gross_volume

# Get all columns with relation to floors:
MATCH (n:IfcBuildingStorey)<-[:RelatingStructure]-(ss:IfcRelContainedInSpatialStructure)-[:RelatedElements]->(c:IfcColumn)
RETURN n, ss, c

# What are the materials used for beams?
MATCH (mt:IfcMaterial)<-[:RelatingMaterial]-(ascmat:IfcRelAssociatesMaterial)-[:RelatedObjects]->(bm:IfcBeam)
RETURN mt

# What objects were made by materials?
MATCH (m:IfcMaterial)<-[:RelatingMaterial]-(asm:IfcRelAssociatesMaterial)-[:RelatedObjects]->(o)
RETURN o

# What spaces are in floors?
MATCH (IfcBuildingStorey)<-[:RelatingObject]-(:IfcRelAggregates)-[:RelatedObjects]->(s:IfcSpace)
RETURN s

# Count beams by type:
MATCH (b:IfcBeam)
RETURN b.ObjectType AS object_type, COUNT(b) AS count
ORDER BY count DESC

# Count columns by type:
MATCH (b:IfcColumn)
RETURN b.ObjectType AS object_type, COUNT(b) AS count
ORDER BY count DESC

# Count walls by type:
MATCH (b:IfcWall)
RETURN b.ObjectType AS object_type, COUNT(b) AS count
ORDER BY count DESC

# Get the building's floor/storey sequence, Storey Level, Storey Elevation, and Storey Name:
MATCH (storey:IfcBuildingStorey)
WHERE storey.Elevation IS NOT NULL
WITH storey
ORDER BY storey.Elevation ASC
WITH collect(storey) AS sortedStoreys
UNWIND range(0, size(sortedStoreys) - 1) AS idx
WITH idx, sortedStoreys[idx] AS storey, sortedStoreys
RETURN CASE
  WHEN storey.Elevation < 0 THEN -1 * (size([s IN sortedStoreys WHERE s.Elevation < 0]) - idx)
  WHEN storey.Elevation = 0 THEN 0
  ELSE idx - size([s IN sortedStoreys WHERE s.Elevation < 0])
END AS StoreyLevel, idx + 1 AS StoreySequence, storey.Name AS StoreyName, storey.Elevation AS Elevation
ORDER BY storey.Elevation ASC

# What are the relations between IfcBuilding and IfcBuildingStorey storeys?
MATCH (b:IfcBuilding)<-[:RelatingObject]-(:IfcRelAggregates)-[:RelatedObjects]->(bs:IfcBuildingStorey)
RETURN bs

# Get the building top floor/storey name:
MATCH (storey:IfcBuildingStorey)
WHERE storey.Elevation IS NOT NULL
WITH storey
ORDER BY storey.Elevation DESC
LIMIT 1
RETURN storey.Name AS TopStoreyName

# Get the storey level of the middle storey:
MATCH (storey:IfcBuildingStorey)
WHERE storey.Elevation IS NOT NULL
WITH storey
ORDER BY storey.Elevation ASC
WITH collect(storey) AS sortedStoreys
WITH sortedStoreys, size(sortedStoreys) AS totalCount
WITH sortedStoreys, totalCount, floor(totalCount / 2.0) AS middleIndex
RETURN sortedStoreys[toInteger(middleIndex)] AS middleStorey, sortedStoreys[toInteger(middleIndex)].Name AS StoreyName, sortedStoreys[toInteger(middleIndex)].Elevation AS Elevation

# Get the number of columns, sum of column volume, sum of beam volume, average of beam volume, average of column volume for each storey of the building, mentioning the storey name and elevation ordered by elevation:
MATCH (storey:IfcBuildingStorey)<-[:RelatingStructure]-(ss:IfcRelContainedInSpatialStructure)-[:RelatedElements]->(c:IfcColumn)
OPTIONAL MATCH (c)<-[:RelatedObjects]-(eq:IfcRelDefinesByProperties)-[:RelatingPropertyDefinition]->(ev:IfcElementQuantity)-[:Quantities]->(qv:IfcQuantityVolume)
WITH storey, count(c) AS column_count, sum(qv.VolumeValue) AS column_volume_sum, storey.Name AS storey_name, storey.Elevation AS storey_elevation
OPTIONAL MATCH (storey)<-[:RelatingStructure]-()-[:RelatedElements]->(b:IfcBeam)
OPTIONAL MATCH (b)<-[:RelatedObjects]-()-[:RelatingPropertyDefinition]->(ev:IfcElementQuantity)-[:Quantities]->(qv:IfcQuantityVolume)
WITH storey, column_count, column_volume_sum, storey_name, storey_elevation, count(b) AS beam_count, sum(qv.VolumeValue) AS beam_volume_sum
RETURN storey_name, storey_elevation, column_count, column_volume_sum, beam_count, beam_volume_sum,
CASE WHEN beam_count > 0 THEN beam_volume_sum / beam_count ELSE 0 END AS beam_volume_avg,
CASE WHEN column_count > 0 THEN column_volume_sum / column_count ELSE 0 END AS column_volume_avg
ORDER BY storey_elevation ASC

# Get materials of slab type:
MATCH (m)<-[:Material]-(ml:IfcMaterialLayer)<-[:MaterialLayers]-(:IfcMaterialLayerSet)<-[:RelatingMaterial]-(:IfcRelAssociatesMaterial)-[:RelatedObjects]->(st:IfcSlabType)
RETURN m, st

# Get all elements that use steel:
MATCH (m:IfcMaterial)<-[:RelatingMaterial]-(ascmat:IfcRelAssociatesMaterial)-[:RelatedObjects]->(o)
WHERE toLower(m.Name) CONTAINS 'steel'
RETURN o

# Get element, element type, element entity and its related implicit quantity names (e.g., GrossVolume, length, area) and their corresponding quantity values:
MATCH (e)<-[:RelatedObjects]-(rdbp:IfcRelDefinesByProperties)-[:RelatingPropertyDefinition]->(eq:IfcElementQuantity)-[:Quantities]->(q)
WITH e, eq, q, LABELS(e)[0] AS element_entity, PROPERTIES(q) AS qProps
RETURN e.Name AS elementName, element_entity, e.ObjectType AS element_type, q.Name AS quantity_property_name,
CASE WHEN size(keys(qProps)) >= 2 THEN qProps[keys(qProps)[1]] ELSE null END AS quantity_property_value


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

#if "USER_OPENAI_API_KEY" in st.session_state:
#    openai_key = st.session_state["USER_OPENAI_API_KEY"]
#else:
#    openai_key = st.secrets["OPENAI_API_KEY"]

graph = Neo4jGraph(
    url=url,
    username=username,
    password=password,
    sanitize = True
)
import os
cypher_llm=None
qa_llm=None
model_name=os.getenv('GPT_MODEL_NAME')
if "gemini" in model_name:
    google_api_key=os.getenv('GOOGLE_API_KEY')
    cypher_llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=google_api_key,temperature=0, verbose=True,top_k=200)
    qa_llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=google_api_key,temperature=0, verbose=True,top_k=200)
else:
    cypher_llm = ChatOpenAI(model=os.getenv('GPT_MODEL_NAME'), temperature=0)
    qa_llm= ChatOpenAI(model=os.getenv('GPT_MODEL_NAME'), temperature=0)
# Official API doc for GraphCypherQAChain at: https://api.python.langchain.com/en/latest/chains/langchain.chains.graph_qa.base.GraphQAChain.html#
graph_chain = GraphCypherQAChain.from_llm(
    cypher_llm=cypher_llm,
    qa_llm=qa_llm,
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
