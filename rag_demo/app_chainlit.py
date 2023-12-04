import chainlit as cl
from chainlit.input_widget import TextInput
import logging
from uploaders import langchain_csv, langchain_image, langchain_json, langchain_txt, langchain_pdf

import os
from dotenv import load_dotenv


# Initial Setup
@cl.on_chat_start
async def start():

    # Load credentials from .env - if present
    load_dotenv(".env")
    url = os.getenv("NEO4J_URI", "")
    username = os.getenv("NEO4J_USERNAME", "")
    password = os.getenv("NEO4J_PASSWORD", "")
    openai = os.getenv("OPENAI_API_KEY", "")

    # Allow user to override credentials or provide if not available
    _ = await cl.ChatSettings(
        [
            TextInput(id="n4j_uri", label="Database URI", initial=url),
            TextInput(id="n4j_user", label="Database User", initial=username),
            TextInput(id="n4j_pass", label="Database Password", initial=password),
            TextInput(id="openai_key", label="OpenAI Key", initial=openai),
        ]
    ).send()

    # Wait for the user to upload a file
    files = None
    while files == None:
        # More info on acceptable mime types: https://www.iana.org/assignments/media-types/media-types.xhtml#text
        files = await cl.AskFileMessage(
            content="Please upload files to begin!", accept=["application/json", "application/pdf", "image/jpeg", "image/png", "text/csv", "text/plain"]
        ).send()

    # Import each file by type
    # More info on file object type from AskFileMessage: https://docs.chainlit.io/api-reference/ask/ask-for-file
    for file in files:
        # More info on file objects: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/file#getting_information_on_selected_files
        logging.info(f'type: {file.type} - {type(file.content)}')

        # Route the file to the appropriate upload function
        # TODO: Easier to follow than a factory method?
        if file.type == "application/json":
            langchain_json.upload(file.content)
        elif file.type == "application/pdf":
            langchain_pdf.upload(file.content)
        elif file.type == "image/jpeg" or file.type == "image/png":
            langchain_image.upload(file.content)
        elif file.type == "text/csv":
            langchain_csv.upload(file.content)
        elif file.type == "text/plain":
            await langchain_txt.upload(file.content)
        else:
            cl.Message(
                content=f"Sorry, we don't support that file type: {file.type}"
            ).send()

    # Let the user know that the system is ready``
    await cl.Message(
        content=f"`Files uploaded!"
    ).send()

    # TODO: Start displaying data when upload is complete
    # TODO: Update displayed data as new data uploaded / added


# When user sends a message
@cl.on_message
async def main(message: cl.Message):
    # Your custom logic goes here...

    # Send a response back to the user
    await cl.Message(
        content=f"Received: {message.content}",
    ).send()


# When chat settings are updated
@cl.on_settings_update
async def setup_agent(settings):
    logging.info("on_settings_update", settings)

    url = settings["n4j_uri"]
    username = settings["n4j_user"]
    password = settings["n4j_pass"]
    openai = settings["openai_key"]

    # Remap updates to environ
    os.environ["NEO4J_URL"] = url
    os.environ["NEO4J_USERNAME"] = username
    os.environ["NEO4J_PASSWORD"] = password
    os.environ["OPENAI_API_KEY"] = openai