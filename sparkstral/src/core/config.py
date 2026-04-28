from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    MISTRAL_API_KEY: str
    DEPLOYMENT_NAME: str
    WEB_SEARCH_MODEL: str
    WEB_SEARCH_MAX_ROUNDS: int
    GENAI_USE_CASES_MODEL: str
    USE_CASE_GRADER_AGENT_MODEL: str
    MARKDOWN_REPORTER_AGENT_MODEL: str
    GENAI_USE_CASES_LLM_TEMPERATURE: float
    LLM_MAX_TOKENS: int
    LLM_TEMPERATURE: float
    FACT_CHECK_MODEL: str


settings = Settings()  # type: ignore[call-arg]
