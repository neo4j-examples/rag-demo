import json


async def upload(file: any):
    """
    Uploads a JSON file to a Neo4j instance.

    Args:
        neo4j_credits: Tuple containing the hostname, username, and password of the target Neo4j instance

        nodes: A dictionary of objects to upload. Each key is a unique node label and contains a list of records as dictionary objects.
    
    Raises:
        Exceptions if data is not in the correct format or if the upload fails.
    """
    data = json.loads(file.content)
