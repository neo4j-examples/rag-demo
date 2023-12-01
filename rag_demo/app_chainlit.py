import chainlit as cl
from chainlit.input_widget import TextInput
import logging
from uploaders import langchain_csv, langchain_image, langchain_json, langchain_pdf
import os
from dotenv import load_dotenv


@cl.on_chat_start
async def start():

    # Load credentials from .env - if present
    load_dotenv(".env")
    url = os.getenv("NEO4J_URI", "")
    username = os.getenv("NEO4J_USERNAME", "")
    password = os.getenv("NEO4J_PASSWORD", "")
    openai = os.getenv("NEO4J_PASSWORD", "")

    # Allow user to override credentials or povide if not available
    _ = await cl.ChatSettings(
        [
            TextInput(id="n4j_uri", label="Database URI", initial="test"),
            TextInput(id="n4j_user", label="Database User", initial=username),
            TextInput(id="n4j_pass", label="Database Password", initial=password),
            TextInput(id="openai_key", label="OpenAI Key", initial=openai),
        ]
    ).send()



    # Ask the user to upload a file
    files = None

    # Wait for the user to upload a file
    while files == None:
        # More info on acceptable mime types: https://www.iana.org/assignments/media-types/media-types.xhtml#text
        files = await cl.AskFileMessage(
            content="Please upload files to begin!", accept=["application/json", "application/pdf", "image/jpeg", "image/png", "text/csv", "text/plain"]
        ).send()

    # Import each file by type
    # More info on file object type from AskFileMessage: https://docs.chainlit.io/api-reference/ask/ask-for-file
    for file in files:
        # More info on file objects: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/file#getting_information_on_selected_files
        logging.info(f'type: {file.type}')

        # Route the file to the appropriate import function
        if file.type == "application/json":
            await langchain_json.upload(file)
        elif file.type == "application/pdf":
            await langchain_pdf.upload(file)
        elif file.type == "image/jpeg" or file.type == "image/png":
            await langchain_image.upload(file)
        elif file.type == "text/csv":
            await langchain_csv.upload(file)
        else:
            await cl.Message(
                content=f"Sorry, we don't support that file type: {file.type}"
            ).send()

    # Let the user know that the system is ready
    await cl.Message(
        content=f"`Files uploaded!"
    ).send()



@cl.on_settings_update
async def setup_agent(settings):
    logging.info("on_settings_update", settings)

    url = settings["n4j_uri"]
    username = settings["n4j_user"]
    password = settings["n4j_pass"]
    openai = settings["openai_key"]


    # Remapping for Langchain Neo4j integration
    os.environ["NEO4J_URL"] = url
    os.environ["OPENAI_API_KEY"] = openai