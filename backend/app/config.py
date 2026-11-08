from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)

    # ── CORS ─────────────────────────────────────────
    allowed_origins: str = Field(default="http://localhost:5173")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    # ── Vultr Serverless Inference ────────────────────
    vultr_inference_base_url: str = Field(default="https://api.vultrinference.com/v1")
    vultr_inference_api_key: str = Field(default="")
    vultr_model_name: str = Field(default="deepseek-v4.1-flash-1017")

    # ── Firebase ─────────────────────────────────────
    firebase_service_account_path: str = Field(default="firebase-service-account.json")

    # ── Upload ───────────────────────────────────────
    max_csv_size_mb: int = Field(default=10)

    @property
    def max_csv_size_bytes(self) -> int:
        return self.max_csv_size_mb * 1024 * 1024

    # ── Sandbox ──────────────────────────────────────
    sandbox_image: str = Field(default="datapilot-sandbox:latest")
    sandbox_timeout_seconds: int = Field(default=30)
    sandbox_max_concurrent: int = Field(default=5)
    sandbox_memory_limit: str = Field(default="256m")
    sandbox_cpu_limit: float = Field(default=0.5)
    sandbox_pids_limit: int = Field(default=50)

    # ── Temp Storage ─────────────────────────────────
    temp_dir: str = Field(default="/tmp/datapilot")


# Single shared instance — import this everywhere
settings = Settings()
