from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./raydot.db"
    SECRET_KEY: str = "change-me-in-production"
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = "raydot"
    MQTT_PASSWORD: str = "raydot"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SCHOOL_EMAIL_DOMAIN: str = "school.edu"
    QR_EXPIRE_MINUTES: int = 30
    JWT_EXPIRE_MINUTES: int = 60
    ADMIN_JWT_EXPIRE_MINUTES: int = 480

    class Config:
        env_file = ".env"


settings = Settings()
