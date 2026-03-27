from pydantic_settings import BaseSettings, SettingsConfigDict


class StrategySettings(BaseSettings):
    kafka_bootstrap_servers: str = 'localhost:9092'
    reports_dir: str = 'strategy_service/reports'
    data_dir: str = 'strategy_service/data'

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = StrategySettings()
