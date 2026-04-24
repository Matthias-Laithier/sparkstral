from pydantic import BaseModel, Field


class WebSearchLookupIn(BaseModel):
    query: str = Field(..., min_length=1, description="Exact search query to look up.")


class WebSearchLookupOut(BaseModel):
    found: bool
    result: str | None = None


class WebSearchStoreIn(BaseModel):
    query: str = Field(..., min_length=1)
    result: str = Field(..., min_length=0)
