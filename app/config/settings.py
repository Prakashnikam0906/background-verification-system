# app/config/settings.py

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "Background Verification System"
    VERSION: str = "1.0.0"
    PORT: int = int(os.getenv("PORT", 8000))

    # UltraSafe - openai compatible api
    ULTRASAFE_API_KEY: str = os.getenv("ULTRASAFE_API_KEY", "")
    ULTRASAFE_BASE_URL: str = os.getenv("ULTRASAFE_BASE_URL", "https://api.ultrasafe.ai/v1")
    ULTRASAFE_MODEL: str = os.getenv("ULTRASAFE_MODEL", "gpt-4o")

    # when false -> uses mock simulation (for demo without credits)
    # when true  -> calls real ultrasafe api using openai client
    USE_REAL_API: bool = os.getenv("USE_REAL_API", "false").lower() == "true"

    AGENT_TIMEOUT: int = 30  # seconds


settings = Settings()
