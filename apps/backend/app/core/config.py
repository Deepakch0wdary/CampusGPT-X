import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CampusGPT X"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    DATABASE_URL: str
    DATABASE_MODE: str = "mysql"
    CORS_ORIGINS: Union[str, List[str]] = []
    SECRET_KEY: str = "supersecretkeycampusgptx2026forlocaldevonly!!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str) -> str:
        import os
        mode = os.environ.get("DATABASE_MODE")
        if not mode:
            # Try reading .env from current directory
            for path in [".env", "apps/backend/.env", "../.env", "../../.env"]:
                try:
                    if os.path.exists(path):
                        with open(path, "r") as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith("#"):
                                    parts = line.split("=", 1)
                                    if len(parts) == 2 and parts[0].strip() == "DATABASE_MODE":
                                        mode = parts[1].strip().strip('"').strip("'")
                                        break
                    if mode:
                        break
                except Exception:
                    pass
        if not mode:
            mode = "mysql"

        if mode == "sqlite_demo":
            return "sqlite:///c:/Users/DELL/OneDrive/Desktop/CampusGPT/apps/backend/campusgpt.db"
        if isinstance(v, str) and v.startswith("mysql://"):
            return v.replace("mysql://", "mysql+pymysql://", 1)
        return v


    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
