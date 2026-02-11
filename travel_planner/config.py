from pydantic import BaseSettings

class Settings(BaseSettings):
    AMADEUS_CLIENT_ID: str | None = None
    AMADEUS_CLIENT_SECRET: str | None = None

    AGODA_API_KEY: str | None = None

    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    USER_AGENT: str = "TravelPlannerBot/1.0"
    DEFAULT_PASSENGERS: int = 1

    class Config:
        env_file = ".env"

settings = Settings()
