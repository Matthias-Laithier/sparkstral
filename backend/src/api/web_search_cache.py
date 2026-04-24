from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.db.engine import get_db
from src.db.models import WebSearchCacheEntry
from src.schemas.web_search_cache import (
    WebSearchLookupIn,
    WebSearchLookupOut,
    WebSearchStoreIn,
)

router = APIRouter(prefix="/web-search-cache", tags=["web_search_cache"])


@router.post("/lookup", response_model=WebSearchLookupOut)
def lookup(
    body: WebSearchLookupIn, db: Session = Depends(get_db)
) -> WebSearchLookupOut:
    row = db.get(WebSearchCacheEntry, body.query)
    if row is None:
        return WebSearchLookupOut(found=False)
    return WebSearchLookupOut(found=True, result=row.result)


@router.post("", status_code=204)
def store(body: WebSearchStoreIn, db: Session = Depends(get_db)) -> None:
    db.merge(
        WebSearchCacheEntry(
            query=body.query,
            result=body.result,
        )
    )
    db.commit()
