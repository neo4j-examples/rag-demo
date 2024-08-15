from constants import SCHEMA_IMG_PATH, LANGCHAIN_IMG_PATH
import streamlit as st
import streamlit.components.v1 as components
from langchain_community.graphs import Neo4jGraph
from neo4j import GraphDatabase
import json
import networkx as nx
from pyvis.network import Network

url = st.secrets["NEO4J_URI"]
username = st.secrets["NEO4J_USERNAME"]
password = st.secrets["NEO4J_PASSWORD"]

neo4j_conn = GraphDatabase.driver(
    uri=url, auth=(username, password)
 )
def fetch_data(query):
    with neo4j_conn.session() as session:
        result = session.run(query)
        return [record for record in result]



# Streamlit app layout
st.title("Neo4j Graph Visualization")

# Example query to fetch data

# Optionally visualize graph data using third-party libraries
import networkx as nx
import matplotlib.pyplot as plt

# Get all secrets
models_dct = {v: k.split("_")[3] + "_API_KEY" for  k,v in st.secrets.items() if "GPT_MODEL_NAME" in k }
print (models_dct)

def ChangeButtonColour(wgt_txt, wch_hex_colour = '12px'):
    htmlstr = """<script>var elements = window.parent.document.querySelectorAll('*'), i;
                for (i = 0; i < elements.length; ++i) 
                    { if (elements[i].innerText == |wgt_txt|) 
                        { elements[i].style.color ='""" + wch_hex_colour + """'; } }</script>  """

    htmlstr = htmlstr.replace('|wgt_txt|', "'" + wgt_txt + "'")
    components.html(f"{htmlstr}", height=0, width=0)

def sidebar():
    with st.sidebar:
        model_name=list(models_dct.keys())[0] if "GPT_MODEL_NAME" not in st.session_state else st.session_state["GPT_MODEL_NAME"] 
        remaining_free_queries=st.session_state["FREE_QUESTIONS_REMAINING"] if "FREE_QUESTIONS_REMAINING" in st.session_state else st.secrets["FREE_QUESTIONS_PER_SESSION"]
        st.write(f"remaining free quoata is: {remaining_free_queries} free questions")
        with st.expander(f"""Model Key- (needed after free quota is exahusted)"""):
            new_oak = st.text_input("Your API Key")
            # if "USER_OPENAI_API_KEY" not in st.session_state:
            #     st.session_state["USER_OPENAI_API_KEY"] = new_oak
            # else:
            st.session_state["USER_OPENAI_API_KEY"] = new_oak
            # Streamlit app layout
            st.title("Neo4j Graph Visualization with Relationships")

        model_name = st.selectbox(
            "select model- beaware: no free quote for gpt-4o!!",
            models_dct.keys(),
        )

        st.write("You selected:", model_name , models_dct[model_name])
        st.session_state["MODEL_API_KEY_TYPE"]=models_dct[model_name]
        st.session_state["GPT_MODEL_NAME"]=model_name


        # Streamlit app
        st.title('Graph Visualization')
        G = nx.Graph()

        # Example query to fetch data
        query = """
        MATCH (n:IfcRelAggregates)-[r:RelatedObjects]->(m:IfcBuildingStorey)
            RETURN n, r, m limit 3
        """
        results = fetch_data(query)
            
        for record in results:
            node1 = record["n"]
            node2 = record["m"]
            relationship = record["r"]
            G.add_node(node1["nid"], label=list(node1.labels)[0], properties=dict(node1))
            G.add_node(node2["nid"], label=list(node2.labels)[0], properties=dict(node2))
            G.add_edge(node1["nid"], node2["nid"], label=relationship.type, properties=dict(relationship))
        net = Network(notebook=False, height="750px", width="100%", bgcolor="#222222", font_color="white", cdn_resources='remote')
 
        net.from_nx(G)
        html_content = net.generate_html(notebook=False)
        st.components.v1.html(html_content, height=750) 

        st.markdown("""Questions you can ask of the dataset:""", unsafe_allow_html=True)

        # To style buttons closer together
        st.markdown("""
                    <style>
                        div[data-testid="column"] {
                            width: fit-content !important;
                            flex: unset;
                        }
                        div[data-testid="column"] * {
                            width: fit-content !important;
                        }
                    </style>
                    """, unsafe_allow_html=True)
        
        sample_questions = "How many storeys in the building?", "כמה קורות יש בקומה 15","מהן ששת הקומות הראשונות?","מה נפח הקורות הכולל בבניין?", "What is the total length of the column in the building?", "מהי הקומה האמצעית בבניין?", "מה נפח הקורות בקומה הגבוהה ביותר? מה שמה ? ומה גובהה?"

        for text, col in zip(sample_questions, st.columns(len(sample_questions))):
            if col.button(text, key=text):
                st.session_state["sample"] = text
