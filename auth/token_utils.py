from datetime import timedelta
from auth.auth_manager import AuthManager

auth_manager = AuthManager()

def create_access_token(user_id: int):
    return auth_manager.create_access_token(
        data={"user_id": user_id}, 
        expires_delta=timedelta(minutes=AuthManager.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

def create_refresh_token(user_id: int):
    return auth_manager.create_refresh_token(
        data={"user_id": user_id}
    )

def decode_token(token: str):
    return auth_manager.decode_token(token)