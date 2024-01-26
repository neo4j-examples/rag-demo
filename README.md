# Neo4j RAG Demo
This sample application demonstrates how to implement a Large Language Model (LLM) and Retrieval Augmented Generation (RAG) system using a Neo4j Graph Database.

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

## GCloud Update
First Install gcloud CLI, then:
```
gcloud auth login
gcloud init
gcloud builds submit --tag gcr.io/<gcloud_project_id>/streamlit-app
gcloud run deploy --image gcr.io/<gcloud_project_id>/streamlit-app --platform managed --allow-unauthenticated
```
First time setup will require a lot of intermediate set up and possible Google console updates + an active Billing account associated with the target project

Gcloud will read from the Dockerfile, app.yaml, and requirements.txt files as configuration files.