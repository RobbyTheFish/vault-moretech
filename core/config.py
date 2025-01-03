import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    TYPE_DB_SECRET = os.getenv("TYPE_DB_SECRET")
    TYPE_ENCRYPT = os.getenv("TYPE_ENCRYPT")
    MASTER_KEY = os.getenv("MASTER_KEY")
