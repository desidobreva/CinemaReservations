from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Cinema Reservations API"
    jwt_secret: str = "CHANGE_ME_SUPER_SECRET"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60 * 24
    database_url: str = "sqlite:///./cinema.db"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60


settings = Settings()
