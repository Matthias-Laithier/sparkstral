import os
import sys
from pathlib import Path

os.environ.setdefault("MISTRAL_API_KEY", "test-mistral-api-key")
os.environ.setdefault("DEPLOYMENT_NAME", "test-deployment")
os.environ.setdefault("WEB_SEARCH_MODEL", "mistral-small-latest")
os.environ.setdefault("WEB_SEARCH_MAX_ROUNDS", "2")
os.environ.setdefault("GENAI_USE_CASES_MODEL", "mistral-medium-latest")
os.environ.setdefault("USE_CASE_GRADER_AGENT_MODEL", "mistral-medium-latest")
os.environ.setdefault("MARKDOWN_REPORTER_AGENT_MODEL", "mistral-medium-latest")
os.environ.setdefault("GENAI_USE_CASES_LLM_TEMPERATURE", "1")
os.environ.setdefault("LLM_MAX_TOKENS", "2048")
os.environ.setdefault("LLM_TEMPERATURE", "0")
os.environ.setdefault("FACT_CHECK_MODEL", "mistral-medium-latest")

sys.path.insert(0, str(Path(__file__).parents[1]))
