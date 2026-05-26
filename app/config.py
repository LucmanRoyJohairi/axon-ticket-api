from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Field names must match .env keys (case-insensitive by default)
    database_url: str

    # This tells from Pydantic to read from a .env file
    model_config = SettingsConfigDict(env_file=".env")


# Creating a Singleton instance to use throughout the app
settings = Settings()