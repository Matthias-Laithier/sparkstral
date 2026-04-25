from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    MISTRAL_API_KEY: str
    DEPLOYMENT_NAME: str
    BACKEND_BASE_URL: str
    SERPER_API_KEY: str
    WEB_SEARCH_MODEL: str
    WEB_SEARCH_MAX_ROUNDS: int
    COMPANY_RESOLVER_AGENT_MODEL: str
    COMPANY_PROFILER_AGENT_MODEL: str
    PAIN_POINT_PROFILER_AGENT_MODEL: str
    OPPORTUNITY_MAPPER_AGENT_MODEL: str
    GENAI_USE_CASES_MODEL: str
    USE_CASE_DEDUPER_AGENT_MODEL: str
    USE_CASE_GRADER_AGENT_MODEL: str
    RED_TEAM_AGENT_MODEL: str
    GENAI_USE_CASES_LLM_TEMPERATURE: float
    LLM_MAX_TOKENS: int
    LLM_TEMPERATURE: float


settings = Settings()  # type: ignore[call-arg]
