import os
import sys
from pathlib import Path

# Settings are loaded at import time; tests must not require a real .env
os.environ.setdefault("MISTRAL_API_KEY", "test-mistral-api-key")
os.environ.setdefault("DEPLOYMENT_NAME", "test-deployment")

sys.path.insert(0, str(Path(__file__).parent))
