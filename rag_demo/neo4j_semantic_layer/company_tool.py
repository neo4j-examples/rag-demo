from typing import Optional, Type

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

# Import things that are needed generically
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool

from neo4j_semantic_layer.utils import get_candidates, graph

description_query = """
MATCH (com:Company)
WHERE com.name = $candidate
RETURN com.name + " is a nice company" AS context LIMIT 1
"""


def get_information(entity: str, type: str) -> str:
    candidates = get_candidates(entity, type)
    if not candidates:
        return "No information was found about the company in the knowledge graph"
    elif len(candidates) > 1:
        newline = "\n"
        return (
            "Need additional information, which of these "
            f"did you mean: {newline + newline.join(str(d) for d in candidates)}"
        )
    data = graph.query(
        description_query, params={"candidate": candidates[0]["candidate"]}
    )
    return data[0]["context"]


class CompanyInput(BaseModel):
    entity: str = Field(description="company or business mentioned in the question")
    entity_type: str = Field(
        description="type of the entity. Must be 'company'"
    )


class CompanyTool(BaseTool):
    name = "company"
    description = (
        "useful for when you need to answer questions about a business or company"
    )
    args_schema: Type[BaseModel] = CompanyInput

    def _run(
        self,
        entity: str,
        entity_type: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        return get_information(entity, entity_type)

    async def _arun(
        self,
        entity: str,
        entity_type: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        return get_information(entity, entity_type)
