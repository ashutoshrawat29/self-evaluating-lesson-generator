import os
from dotenv import load_dotenv

load_dotenv()


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash"
)

MAX_RETRIES = 2

DATABASE_PATH = "data/memory.db"

DEMO_FAILURE = (
    os.getenv("DEMO_FAILURE", "false").lower()
    == "true"
)


if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing."
    )