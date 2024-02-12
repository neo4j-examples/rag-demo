# Neo4j RAG Demo
This sample application demonstrates how to implement a Large Language Model (LLM) and Retrieval Augmented Generation (RAG) system with a Neo4j Graph Database. This application uses Streamlit, LangChain, [Neo4jVector](https://python.langchain.com/docs/integrations/vectorstores/neo4jvector) vectorstore and [Neo4j DB QA Chain](https://python.langchain.com/docs/use_cases/graph/graph_cypher_qa)

## Requirements
- [Poetry](https://python-poetry.org) for dependency managament.

## Usage
```
poetry update
poetry run streamlit run rag_demo/main.py --server.port=80

OR

pipenv shell
pipenv install
pipenv run streamlit run rag_demo/main.py
```