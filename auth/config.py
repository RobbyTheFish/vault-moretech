import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv("MONGO_AUTH_URI")
MONGO_DB_NAME = os.getenv("MONGO_AUTH_DB_NAME")


JWT_SECRET = os.getenv("JWT_SECRET", "jwtjwtjwtjwtjwt")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


LDAP_SERVER = os.getenv("LDAP_SERVER")
LDAP_BIND_DN = os.getenv("LDAP_BIND_DN")
LDAP_BIND_PASSWORD = os.getenv("LDAP_BIND_PASSWORD")
LDAP_SEARCH_BASE = os.getenv("LDAP_SEARCH_BASE")