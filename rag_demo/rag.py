from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.pydantic_v1 import BaseModel


# add typing for input
class QuestionPrompt(BaseModel):
    question: str


# utility for formatting retrieved data
def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])


def generate_chain(retriever, model, prompt):
    return (
            {
                "context": itemgetter("question") | retriever | format_docs,
                "question": itemgetter("question")
            }
            | prompt
            | model
            | StrOutputParser()
    )
