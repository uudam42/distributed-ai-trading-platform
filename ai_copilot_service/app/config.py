from pydantic_settings import BaseSettings, SettingsConfigDict


class CopilotSettings(BaseSettings):
    kafka_bootstrap_servers: str = 'localhost:9092'
    vllm_base_url: str = 'http://localhost:8000/v1'
    vllm_model: str = 'Qwen/Qwen2.5-7B-Instruct'
    ai_mock_mode: bool = False
    ai_timeout_seconds: int = 20

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = CopilotSettings()
