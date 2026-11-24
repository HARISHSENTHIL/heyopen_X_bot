from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    x_consumer_key: str
    x_consumer_secret: str
    x_bearer_token: str
    x_access_token: str
    x_access_token_secret: str

    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-5-5"

    poll_interval_seconds: int = 30
    max_replies_per_day: int = 200
    max_replies_per_author_per_day: int = 5
    require_verified_author: bool = True
    require_us_author: bool = True
    db_path: str = "./data/bot.db"


settings = Settings()
