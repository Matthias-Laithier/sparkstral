from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    MISTRAL_API_KEY: str
    DEPLOYMENT_NAME: str
    SERPER_API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None
    WEB_SEARCH_PROVIDER: Literal["serper", "mistralai", "tavily"] = "serper"
    WEB_SEARCH_MODEL: str
    WEB_SEARCH_MAX_ROUNDS: int
    COMPANY_RESOLVER_AGENT_MODEL: str
    GENAI_USE_CASES_MODEL: str
    USE_CASE_GRADER_AGENT_MODEL: str
    MARKDOWN_REPORTER_AGENT_MODEL: str
    GENAI_USE_CASES_LLM_TEMPERATURE: float
    LLM_MAX_TOKENS: int
    LLM_TEMPERATURE: float
    RESOLVER_LLM_MAX_TOKENS: int = 4096
    GRADER_LLM_MAX_TOKENS: int = 4096

    @model_validator(mode="after")
    def require_search_provider_key(self) -> Self:
        if self.WEB_SEARCH_PROVIDER == "serper" and not self.SERPER_API_KEY:
            raise ValueError(
                "SERPER_API_KEY is required when WEB_SEARCH_PROVIDER=serper"
            )
        if self.WEB_SEARCH_PROVIDER == "tavily" and not self.TAVILY_API_KEY:
            raise ValueError(
                "TAVILY_API_KEY is required when WEB_SEARCH_PROVIDER=tavily"
            )
        return self


settings = Settings()  # type: ignore[call-arg]
