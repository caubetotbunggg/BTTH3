from pydantic import BaseModel

from app.models.retrieve_model import RetrieveResponse


# Retrieve
class Retrieve_tool_request(BaseModel):
    user_input: str
    k: int


class Retrieve_tool_response(BaseModel):
    chunks: RetrieveResponse


# Generate
class Generate_answer_tool_request(BaseModel):
    user_input: str
    chunks: RetrieveResponse


class Generate_answer_tool_response(BaseModel):
    answer: str


# Citation
class Format_citation_tool_request(BaseModel):
    answer: str
    chunks: RetrieveResponse


class Format_citation_tool_response(BaseModel):
    formatted_answer: str
