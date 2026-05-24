from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./northside.db"
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    mail_mode: str = "log"
    timezone_default: str = "UTC"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
