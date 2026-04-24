from enum import Enum

from pydantic import BaseModel, Field


class CompanyResolutionStatus(str, Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"


class CompanyProfileInput(BaseModel):
    company_query: str = Field(..., description="Raw company name entered by the user.")


class EvidenceItem(BaseModel):
    claim: str = Field(
        ..., description="Short factual claim used to build the profile."
    )
    source: str = Field(
        ...,
        description="URL string (https recommended) supporting the claim.",
    )


class CompanyProfileOutput(BaseModel):
    status: CompanyResolutionStatus
    confidence: float = Field(..., ge=0, le=1)
    company_name: str = ""
    industry: str = ""
    business_lines: list[str] = Field(default_factory=list)
    key_customers: list[str] = Field(default_factory=list)
    strategic_priorities: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    notes: str = Field(
        default="",
        description="Explanation for ambiguity, failure, or important caveats.",
    )
