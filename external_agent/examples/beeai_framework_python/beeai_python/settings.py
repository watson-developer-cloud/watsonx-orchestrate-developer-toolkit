from dotenv import load_dotenv
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

__all__ = ["AppSettings"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", str_to_upper=False)

    api_key: str = Field(..., description="Project API Key")
    watsonx_url: str
    watsonx_project_id: str
    watsonx_api_key: str
    tavily_api_key: str
    log_intermediate_steps: bool = Field(default=False)
    watsonx_default_model: str = "ibm/granite-3-3-8b-instruct"


AppSettings = Settings()
