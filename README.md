# Neo4j RAG Demo
This sample application demonstrates how to implement a Large Language Model (LLM) and Retrieval Augmented Generation (RAG) system with a Neo4j Graph Database. This application uses Streamlit, LangChain, [Neo4jVector](https://python.langchain.com/docs/integrations/vectorstores/neo4jvector) vectorstore and [Neo4j DB QA Chain](https://python.langchain.com/docs/use_cases/graph/graph_cypher_qa)

![Alt Text](https://res.cloudinary.com/dk0tizgdn/image/upload/v1707842287/rag-demo-short_vwezew.gif)

## Requirements
- [Poetry](https://python-poetry.org) for dependency managament.
- Duplicate the `secrets.toml.example` file to `secrets.toml` and populate with appropriate keys.

## Usage
```
poetry update
poetry run streamlit run rag_demo/main.py --server.port=80

OR

pipenv shell
pipenv install
pipenv run streamlit run rag_demo/main.py
```

## GCloud Update
A hosted example of the rag-demo can be found at https://dev.neo4j.com/rag-demo. To create and run your own hosted version of this app on Google Cloud:

1. First Install [gcloud CLI](https://cloud.google.com/sdk/docs/install), then:
2. Update the requirements.txt file with `poetry export --without-hashes --format=requirements.txt > requirements.txt`
3. Make sure a copy of the streamlit secrets.toml file is in the root folder path (may have to temp comment out from .gitignore for the gcloud build to properly find the secrets.toml file)
4. Run the following terminal commands
```
gcloud auth login
gcloud init
gcloud builds submit --tag gcr.io/<gcloud_project_id>/streamlit-app
gcloud run deploy --image gcr.io/<gcloud_project_id>/streamlit-app --platform managed --allow-unauthenticated
```