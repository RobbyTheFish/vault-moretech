from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    db_user: str
    db_password: str
    db_host: str
    db_port: int
    db_name: str

    class Config:
        env_file = "core/db_conn/.env"
