# Neo4j RAG Demo
This sample application demonstrates how to implement a Large Language Model (LLM) and Retrieval Augmented Generation (RAG) system using a Neo4j Graph Database.

## Requirements
- [Poetry](https://python-poetry.org) for dependency managament.

## Usage
```
poetry update
poetry run streamlit run rag_demo/Home.py --server.port=80

OR

pipenv shell
pipenv install
pipenv run streamlit run rag_demo/Home.py
```