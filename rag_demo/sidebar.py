from constants import SCHEMA_IMG_PATH, LANGCHAIN_IMG_PATH
import streamlit as st
import streamlit.components.v1 as components
from langchain_community.graphs import Neo4jGraph
from neo4j import GraphDatabase

url = st.secrets["NEO4J_URI"]
username = st.secrets["NEO4J_USERNAME"]
password = st.secrets["NEO4J_PASSWORD"]

neo4j_conn = GraphDatabase.driver(
    uri=url, auth=(username, password)
 )
def fetch_data(query):
    with neo4j_conn.session() as session:
        result = session.run(query)
        return [record.data() for record in result]


# Streamlit app layout
st.title("Neo4j Graph Visualization")

# Example query to fetch data

# Optionally visualize graph data using third-party libraries
import networkx as nx
import matplotlib.pyplot as plt

def draw_graph(data):
    G = nx.Graph()
    
    # Add nodes and edges
    for record in data:
        node_from = record.get('node_from')
        node_to = record.get('node_to')
        
        # Add nodes
        G.add_node(node_from['nid'], label=node_from.get('labels', ''))
        G.add_node(node_to['nid'], label=node_to.get('label', 'Name'))
        
        # Add edge
        G.add_edge(node_from['nid'], node_to['nid'])
    
    # Generate positions for nodes
    pos = nx.spring_layout(G)
    
    # Create a new figure and axes
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Draw the graph
    nx.draw(
        G, 
        pos, 
        with_labels=True, 
        ax=ax, 
        node_size=1000,         # Increase node size
        node_color='lightblue', # Node color
        edge_color='gray',      # Edge color
        font_size=10,          # Font size for labels
        font_weight='bold'     # Font weight for labels
    )
    
    # Return the figure object
    return fig


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
        MATCH (n:IfcBuildingStorey)<-[r]-(m)
        RETURN n AS node_from, m AS node_to
        LIMIT 6
        """
        data = fetch_data(query)

        # Display data
#        st.write("Fetched Data:")
#        st.write(data)

        # Plot the graph
        fig = draw_graph(data)
        st.pyplot(fig)

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
        
        sample_questions = "How many storeys in the building?", "כמה קורות יש בקומה 14","מה נפח הקורות הכולל בבניין?", "Which managers own more than one company?", "מהי הקומה האמצעית בבניין?", "מה נפח הקורות בקומה הגבוהה ביותר? מה שמה ? ומה גובהה?"

        for text, col in zip(sample_questions, st.columns(len(sample_questions))):
            if col.button(text, key=text):
                st.session_state["sample"] = text
