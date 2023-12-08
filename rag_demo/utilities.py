import logging
import sys

def enable_logging():

    # Configure Neo4j's Python driver log output
    handler = logging.StreamHandler(sys.stdout)
    logging.getLogger("neo4j").addHandler(handler)
    logging.getLogger("neo4j").setLevel(logging.INFO)

    # The driver output is extensive, even at the INFO level

    # Set up logging to a file so full output is accessible
    logging.basicConfig(filename='rag_demo.log', encoding='utf-8', level=logging.DEBUG)

    # Add a handler to print to stdout
    logging.getLogger().addHandler(logging.StreamHandler())