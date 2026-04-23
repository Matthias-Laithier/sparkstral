from typing import Any

from pydantic import BaseModel


class CompanyRequest(BaseModel):
    company_name: str


class TriggerResponse(BaseModel):
    execution_id: str
    status: str


class StatusResponse(BaseModel):
    execution_id: str
    status: str
    result: Any = None
