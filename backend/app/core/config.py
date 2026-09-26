from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "WhatsApp Automation API"
    app_env: str = "development"
    api_prefix: str = "/api/v1"

    database_url: str

    whatsapp_verify_token: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_business_account_id: str = ""
    meta_app_secret: str = ""
    whatsapp_api_version: str = "v23.0"

    laya_base_url: str = ""
    laya_api_key: str = ""
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""

    redis_url: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
