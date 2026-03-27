from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "service"
    service_port: int = 8000
    database_url: str = "postgresql://trading:trading@postgres:5432/trading"
    kafka_bootstrap_servers: str = "kafka:9092"
    auth_service_url: str = "http://auth-service:8081"
    order_service_url: str = "http://order-service:8082"
    portfolio_service_url: str = "http://portfolio-service:8085"
    jwt_secret: str = "change-me"
    jwt_issuer: str = "distributed-ai-trading"
    jwt_audience: str = "trading-clients"
    access_token_exp_minutes: int = 60

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()
