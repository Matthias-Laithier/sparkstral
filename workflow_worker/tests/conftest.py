import os
import sys
from pathlib import Path

os.environ.setdefault("MISTRAL_API_KEY", "test-mistral-api-key")
os.environ.setdefault("DEPLOYMENT_NAME", "test-deployment")
os.environ.setdefault("BACKEND_BASE_URL", "http://backend:8000")
os.environ.setdefault("SERPER_API_KEY", "test-serper-api-key")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily-api-key")
os.environ.setdefault("WEB_SEARCH_PROVIDER", "serper")
os.environ.setdefault("WEB_SEARCH_MODEL", "mistral-small-latest")
os.environ.setdefault("WEB_SEARCH_MAX_ROUNDS", "2")
os.environ.setdefault("COMPANY_RESOLVER_AGENT_MODEL", "mistral-medium-latest")
os.environ.setdefault("COMPANY_PROFILER_AGENT_MODEL", "mistral-medium-latest")
os.environ.setdefault("PAIN_POINT_PROFILER_AGENT_MODEL", "mistral-medium-latest")
os.environ.setdefault("OPPORTUNITY_MAPPER_AGENT_MODEL", "mistral-medium-latest")
os.environ.setdefault("GENAI_USE_CASES_MODEL", "mistral-medium-latest")
os.environ.setdefault("USE_CASE_DEDUPER_AGENT_MODEL", "mistral-medium-latest")
os.environ.setdefault("USE_CASE_GRADER_AGENT_MODEL", "mistral-medium-latest")
os.environ.setdefault("RED_TEAM_AGENT_MODEL", "mistral-medium-latest")
os.environ.setdefault("REFINER_AGENT_MODEL", "mistral-medium-latest")
os.environ.setdefault("FINAL_REPORTER_AGENT_MODEL", "mistral-medium-latest")
os.environ.setdefault("MARKDOWN_REPORTER_AGENT_MODEL", "mistral-medium-latest")
os.environ.setdefault("GENAI_USE_CASES_LLM_TEMPERATURE", "1")
os.environ.setdefault("LLM_MAX_TOKENS", "2048")
os.environ.setdefault("LLM_TEMPERATURE", "0")

sys.path.insert(0, str(Path(__file__).parents[1]))
