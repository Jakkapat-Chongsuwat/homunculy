"""Grader Schema Models."""

from pydantic import BaseModel, Field


class GradeDocumentsSchema(BaseModel):
    """Binary score for document relevance."""

    binary_score: str = Field(description="Documents are relevant: 'yes' or 'no'")


class GradeHallucinationsSchema(BaseModel):
    """Binary score for hallucination detection."""

    binary_score: str = Field(description="Answer is grounded in facts: 'yes' or 'no'")


class GradeAnswerSchema(BaseModel):
    """Binary score for answer usefulness."""

    binary_score: str = Field(description="Answer addresses the question: 'yes' or 'no'")
