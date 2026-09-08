import os
import sys
from pathlib import Path

import pytest

#pytest puts the tests folder on sys.path, not the project root, so `pytest`
#cannot see the agents/ and utils/ packages without this. same fix as ui/app.py.
sys.path.append(str(Path(__file__).resolve().parent.parent))

#the agent modules build their chat clients at import time, and those classes
#refuse to be created without an api key. these dummy values only exist so the
#imports go through - not one test in this folder makes a real api call.
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("MISTRAL_API_KEY", "test-key")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("OPENAI_API_KEY", "test-key")


@pytest.fixture
def agent_state():
    """the smallest valid AgentSchema.

    none of the fields have defaults, so without this every test would have to
    repeat all nine of them just to change one. the fixture is rebuilt for each
    test, so changing it inside a test is safe.
    """
    return {
        "curated_prompt": "",
        "messages": [],
        "user_question": "how many rides are in the database",
        "context": "",
        "sql_from_llm": "SELECT COUNT(*) FROM rides;",
        "safe_checker": "No",
        "comments": "",
        "final_sql_out": "",
        "final_ans": "",
    }
