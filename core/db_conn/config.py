from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    secret_db_uri: str
    secret_db_type: str
    secret_db_username: str
    secret_db_password: str
    secret_db_host: str = "None"
    secret_db_port: int
    secret_db_name: str

    class Config:
        env_file = ".env"
        extra = "ignore"


config = Config()
