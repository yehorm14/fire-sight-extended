import os
import sys
from pathlib import Path

import pytest

# load_dotenv() never overrides vars that are already set.
# Pin every env var the tests depend on so a developer's backend/.env cannot change results.
os.environ["OPENAI_API_KEY"] = ""
os.environ["CORS_ORIGINS"] = "http://localhost:5173,http://127.0.0.1:5173"
os.environ.pop("RENDER", None)
os.environ.pop("ENVIRONMENT", None)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402


@pytest.fixture(scope="session")
def client():
    return TestClient(main.app)
