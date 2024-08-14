from constants import SCHEMA_IMG_PATH, LANGCHAIN_IMG_PATH
import streamlit as st
import streamlit.components.v1 as components
from langchain_community.graphs import Neo4jGraph
from neo4j import GraphDatabase
#from data_fetcher import get_neo4j_data
import json

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



def ChangeButtonColour(wgt_txt, wch_hex_colour = '12px'):
    htmlstr = """<script>var elements = window.parent.document.querySelectorAll('*'), i;
                for (i = 0; i < elements.length; ++i) 
                    { if (elements[i].innerText == |wgt_txt|) 
                        { elements[i].style.color ='""" + wch_hex_colour + """'; } }</script>  """

    htmlstr = htmlstr.replace('|wgt_txt|', "'" + wgt_txt + "'")
    components.html(f"{htmlstr}", height=0, width=0)

def sidebar():
    with st.sidebar:

        with st.expander("OpenAI Key"):
            new_oak = st.text_input("Your OpenAI API Key")
            # if "USER_OPENAI_KEY" not in st.session_state:
            #     st.session_state["USER_OPENAI_KEY"] = new_oak
            # else:
            st.session_state["USER_OPENAI_KEY"] = new_oak
            # Streamlit app layout
            st.title("Neo4j Graph Visualization with Relationships")

        # Example query to fetch data
            query = """
            MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT 25
            """
    #    query = """
    #    MATCH (n:IfcBuildingStorey)<-[r]-(m)
    #    RETURN n AS node_from, m AS node_to
    #    LIMIT 6
    #    """
        data = fetch_data(query)
##############################################################
        nodes = []
        links = []
        for record in data:
            node1 = dict(record['n'].items())  # Extract properties from node1
            node2 = dict(record['m'].items())  # Extract properties from node2
            relationship = dict(record['r'].items())  # Extract properties from relationship

            nodes.append({'id': node1['nid'], 'group': 1})
            nodes.append({'id': node2['nid'], 'group': 2})
            links.append({'source': node1['nid'], 'target': node2['nid'],  'relationship': relationship,'value': 1})


        d3_data = {
            'nodes': nodes,
            'links': links,
        }

        # Load HTML template
        with open('/Users/amit/github/rag-demo/rag_demo/d3_template.html', 'r') as file:
            html_template = file.read()

        # Render HTML in Streamlit
        st.components.v1.html(html_template.replace('{{ data | safe }}', json.dumps(d3_data)), height=600, scrolling=True)




        # Display data
#        st.write("Fetched Data:")
#        st.write(data)

        # Plot the graph
#        fig = draw_graph(data)
#        st.pyplot(fig)

#        st.markdown(f"""This the schema in which the EDGAR filings are stored in Neo4j: \n <img style="width: 70%; height: auto;" src="{SCHEMA_IMG_PATH}"/>""", unsafe_allow_html=True)

#        st.markdown(f"""This is how the Chatbot flow goes: \n <img style="width: 70%; height: auto;" src="{LANGCHAIN_IMG_PATH}"/>""", unsafe_allow_html=True)

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
