from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_URL: str
    JWT_SECRET: str
    JWT_EXPIRE: int = 3600

    class Config:
        env_file = ".env"

settings = Settings()
