from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.schema import HumanMessage, SystemMessage
import logging

def get_tags(text: str) -> list[str]:
    chat = ChatOpenAI(temperature=0)
    # chat = ChatOpenAI(temperature=0, openai_api_key="YOUR_API_KEY", openai_organization="YOUR_ORGANIZATION_ID")

    messages = [
        SystemMessage(
            content="You are a helpful assistant that extracts topics from text.",
        ),
        HumanMessage(
            content=f"Extract the top 10 topics or concepts from a body of text. Return only 1-3 word lowercased, singular answers. Do not return plural forms of words. Only return a comma separated list like 'llm, rag, knowledge graph, fraud, supply chain, neo4j, microsoft'. Extract from this text: {text}."
        ),
    ]
    result = chat(messages)
    logging.info(f'Tags generated: {result.content}')
    
    # Process strings if result was as expected - removing topics: header if not
    tags = [x.strip().replace("topics: ","").replace("topics:","").lower() for x in result.content.split(",")]

    # Process strings if result came back as a numbered list
    cleaned = []
    for tag in tags:
        for item in tag.split("."):
            cleaned.append(item.strip().lstrip("0123456789"))

    return cleaned

