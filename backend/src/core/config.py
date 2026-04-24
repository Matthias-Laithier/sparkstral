from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    MISTRAL_API_KEY: str
    COMPANY_PROFILER_SEARCH_MODEL: str
    COMPANY_PROFILER_AGENT_MODEL: str
    PAIN_POINT_PROFILER_SEARCH_MODEL: str
    PAIN_POINT_PROFILER_AGENT_MODEL: str


settings = Settings()  # type: ignore[call-arg]
