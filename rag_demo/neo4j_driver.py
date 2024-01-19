import os
from neo4j import GraphDatabase, Result
import pandas
import streamlit as st

host = st.secrets["NEO4J_URI"]
user = st.secrets["NEO4J_USERNAME"]
password = st.secrets["NEO4J_PASSWORD"]
database = st.secrets["NEO4J_DATABASE"]

def run_query(query, params = {}) -> pandas.DataFrame:
    with GraphDatabase.driver(host, auth=(user, password)) as driver:
        df = driver.execute_query(
            query, 
            params, 
            database=database,
            result_transformer_= Result.to_df
        ) 
        return df
