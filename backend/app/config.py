from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    app_name: str = "Interview BARS System API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./app.db"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    cors_origins: str = "http://127.0.0.1:3000,http://localhost:3000"
    bars_excel_path: str = str(BACKEND_DIR / "data" / "BARS評価項目と面談評価表.xlsx")

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
