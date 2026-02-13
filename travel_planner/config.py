from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AMADEUS_CLIENT_ID: str = "API Key"
    AMADEUS_CLIENT_SECRET: str = "API SECRET"

    SERPAPI_API_KEY: str | None = None

    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    USER_AGENT: str = "TravelPlannerBot/1.0"
    DEFAULT_PASSENGERS: int = 1
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
