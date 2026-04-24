from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  tg_bot_token: str
  groq_api_key: str
  groq_model: str = "llama-3.3-70b-versatile"
  hh_api_url: str = "https://api.hh.ru"
  remotive_api_url: str = "https://remotive.com/api"
  hh_results_limit: int = 5
  request_timeout: int = 20
  easytap_api_url: str = ""
  easytap_web_app_url: str = ""

  model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
