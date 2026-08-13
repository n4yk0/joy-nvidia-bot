from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    telegram_token: str = Field(..., description="BotFather token")
    telegram_chat_id: str = Field(..., description="Destination chat id")

    locale: str = "fr-fr"
    poll_interval: float = 45.0
    poll_jitter: float = 10.0

    state_file: Path = Path("/data/state.json")
    dry_run: bool = False
    log_level: str = "INFO"

    impersonate: str = "chrome"
