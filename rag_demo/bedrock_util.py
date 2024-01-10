import boto3
import streamlit as st
import json

SERVICE_NAME=st.session_state['SERVICE_NAME']
REGION_NAME=st.session_state['REGION_NAME']
bedrock = boto3.client(
 service_name=SERVICE_NAME,
 region_name=REGION_NAME,
 endpoint_url=f'https://{SERVICE_NAME}.{REGION_NAME}.amazonaws.com',
 aws_access_key_id=st.session_state["AWS_ACCESS_KEY"],
 aws_secret_access_key=st.session_state["AWS_SECRET_KEY"]
)

def get_client():
    return bedrock

def call_language_model(prompt_data):
    try:
        body = json.dumps({"prompt": f"Human: {prompt_data} \n Assistant:",
                           "temperature":0,
                           "top_k":1, "top_p":0.88,
                           "anthropic_version":"bedrock-2023-05-31",
                           "max_tokens_to_sample": 2048})
        modelId = 'anthropic.claude-v2' # change this to use a different version from the model provider
        accept = 'application/json'
        contentType = 'application/json'

        response = bedrock.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
        response_body = json.loads(response.get('body').read())

        return response_body.get('completion')
    except Exception as e:
        print(e)
