"""ORM model for the web search result cache (Postgres)."""

from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.engine import Base

WEB_SEARCH_CACHE_TABLE = "web_search_cache"


class WebSearchCacheEntry(Base):
    __tablename__ = WEB_SEARCH_CACHE_TABLE

    query: Mapped[str] = mapped_column(Text, primary_key=True)
    result: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
