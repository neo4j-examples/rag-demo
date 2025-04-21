import json
import logging
import streamlit as st
import urllib.parse
from retry import retry
from langchain.chains import GraphCypherQAChain
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain_community.graphs import Neo4jGraph
from langchain.prompts.prompt import PromptTemplate
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI


CYPHER_GENERATION_TEMPLATE = """
You are a Cypher expert who translates natural language questions into Cypher queries for a Neo4j graph database. 
The database contains entities such as:
- Paper (p)
- Location (l)
- OceanCirculation (oc)
- WeatherEvent (we)
- Teleconnection (t)
- Model or Project (m)

Relationships include:
- :Mention (from Paper to another node), with property: Mention_Sentence
- :TargetsLocation (from a concept like OceanCirculation or WeatherEvent to a Location)

Properties include:
- Name (for all nodes)
- Mention_Sentence (in the :Mention relationship)
- wikidata_description (for Location)

- Ocean circulation processes often target specific oceanic locations, such as the Southern Ocean.
- Mentions of concepts in papers are linked via the :Mention relationship, which includes a Mention_Sentence field.
- To filter by concepts like "upwelling", check if the Mention_Sentence contains that word.
- A common type of question is: "What [scientific concept] are discussed in relation to [location] and involving [mechanism/phenomenon]?"
- The Cypher query often starts by matching a domain concept (e.g., OceanCirculation) and the location it's associated with.
- Then it retrieves papers mentioning that concept, filtering by keywords in the mention sentence.
- **Always use `[m:Mention]` when matching the mention relationship, never `[m]` or `[:Mention]`.**
- **Use labels like `:WeatherEvent`, `:OceanCirculation`, etc., only when the natural language question explicitly refers to the concept. Otherwise, leave the node unlabeled.**
- **Wrap multiple conditions in WHERE clauses (e.g., with OR/AND) inside parentheses to preserve logic clarity.**
- **When using a Location name in a Cypher match, convert it to all uppercase and replace spaces with underscores. (e.g., "North Atlantic" → "NORTH_ATLANTIC")**

Important: Never use [:Mention] in query and Name of Location always uppercase and replace space with _ (example "North Atlantic" becomes "NORTH_ATLANTIC").

The following is the schema of the Neo4j database. The schema is a simplified representation of the graph database, showing the types of nodes and relationships present in the database. The schema includes nodes for Paper, Location, OceanCirculation, WeatherEvent, Teleconnection, and Model or Project, along with their respective properties and relationships.


Schema database is:
{schema}

Here are some examples:

### Example 1
Natural Language Question:
Which papers mention anomalous temperature regimes such as cold air outbreaks (CAOs) or warm waves (WWs) in relation to North America, specifically in the sentences where these terms appear?

Cypher:
MATCH (we)-[:TargetsLocation]-(l{{Name:"NORTH_AMERICA"}}) 
MATCH (p:Paper)-[m:Mention]-(we) 
WHERE m.Mention_Sentence CONTAINS 'WW' OR m.Mention_Sentence CONTAINS 'CAOs' 
RETURN p,l,we;

---

### Example 2
Natural Language Question:
Which papers discuss ocean circulation processes—such as thermohaline circulation—in oceanic regions that include either “North” or “South” in their names?

Cypher:
MATCH (n:Location) 
WHERE n.Name CONTAINS 'OCEAN' AND (n.Name CONTAINS 'NORTH' OR n.Name CONTAINS 'SOUTH') 
MATCH (oc:OceanCirculation)-[:TargetsLocation]-(l) 
MATCH (p:Paper)-[m:Mention]-(oc) 
WHERE m.Mention_Sentence CONTAINS 'thermohaline circulation' 
RETURN n,oc,p;

---

### Example 3
Natural Language Question:
Which papers mention CMIP5 models and the North Atlantic Oscillation (NAO) in the context of the Southeast United States?

Cypher:
MATCH (p:Paper)-[r:Mention]->(m:Model|Project) 
WHERE m.Name CONTAINS 'CMIP_5' 
MATCH (p)-[t:Mention]-(n:Teleconnection{{Name:"NORTH_ATLANTIC_OSCILLATION"}}) 
WHERE t.Mention_Sentence CONTAINS 'Southeast' 
RETURN p,m,n;

---

### Example 4
Natural Language Question:
Which papers mention the Pacific-North American (PNA) pattern in connection with locations in the United States?

Cypher:
MATCH (p:Paper)-[z:Mention]->(t:Teleconnection{{Name:"PACIFIC_NORTH_AMERICAN_PNA_PATTERN"}}) 
MATCH (t)-[:TargetsLocation]-(l:Location) 
MATCH (p)-[z:Mention]-(l) 
WHERE l.wikidata_description CONTAINS "United States" 
RETURN p,t,l;


---

Now generate a Cypher query for:
{question}
"""



CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)

MEMORY = ConversationBufferMemory(
    memory_key="chat_history", 
    input_key='question', 
    output_key='answer', 
    return_messages=True
)

# Neo4j connection
url = st.secrets["NEO4J_URI"]
username = st.secrets["NEO4J_USERNAME"]
password = st.secrets["NEO4J_PASSWORD"]

graph = Neo4jGraph(
    url=url,
    username=username,
    password=password,
    sanitize=True
)


graph_chain = GraphCypherQAChain.from_llm(
    #cypher_llm=ChatOllama(model="qwen2", temperature=0),
    #qa_llm=ChatOllama(model="qwen2", temperature=0),
    cypher_llm=ChatOpenAI(
         openai_api_key=st.secrets["OPENAI_API_KEY"], 
         temperature=0, 
         model_name="gpt-4o-mini"
     ),
     qa_llm=ChatOpenAI(
         openai_api_key=st.secrets["OPENAI_API_KEY"], 
         temperature=0, 
         model_name="gpt-4o-mini"),
    graph=graph,
    cypher_prompt=CYPHER_GENERATION_PROMPT,  
    validate_cypher=True,
    return_direct=True,
    verbose=True,
    allow_dangerous_requests=True,
    return_intermediate_steps=True,
)


@retry(tries=2, delay=12)
def get_results(question) -> str:
    """Generate a response from the GraphCypherQAChain using a cleaned schema and improved prompt."""
    
    logging.info(f'Using Neo4j database at URL: {url}')
    graph.refresh_schema()

    #Log full Neo4j schema in terminal
    #print("\n========= Raw Schema from Neo4j =========\n")
    #print(graph.get_schema)

    prompt = CYPHER_GENERATION_PROMPT.format(schema=graph.get_schema, question=question)
    print('\n========= Prompt to LLM =========\n')
    print(prompt)

    try:
        chain_result = graph_chain.invoke(
            {"query": question},
            prompt=prompt,
            return_only_outputs=True,
        )
    except Exception as e:
        logging.warning(f'Handled exception running GraphCypher chain: {e}')
        return "Sorry, I couldn't find an answer to your question"
    
    if chain_result is None:
        print('No answer was generated.')
        return "No answer was generated."

    # Debug: show Cypher used
    cypher_query = chain_result.get("cypher", "No Cypher returned")
    print("\n========= Generated Answer=========\n")
    print(cypher_query)

    result = chain_result.get("result", None)
    print("\n========= Final Result =========\n")
    print(json.dumps(chain_result, indent=2))
    
    try:
        query = chain_result["intermediate_steps"][-1]["query"].replace("cypher", "", 1).strip()
        chain_result["intermediate_steps"][-1]["query"] = urllib.parse.quote(query)
    except Exception as e:
        pass

    return chain_result
