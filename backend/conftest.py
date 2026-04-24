import os
import sys
from pathlib import Path

# Settings are loaded at import time; tests must not require a real .env
os.environ.setdefault("MISTRAL_API_KEY", "test-mistral-api-key")
os.environ.setdefault("DEPLOYMENT_NAME", "test-deployment")
# Postgres only (no SQLite). Start the DB first, e.g. `docker compose up -d postgres`
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://sparkstral:sparkstral@127.0.0.1:5432/sparkstral",
)

sys.path.insert(0, str(Path(__file__).parent))
