from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import datetime
from typing import Dict, Any, List, TypedDict

from core.config import settings
from app.models.enums import RoleInSystem


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


jwt_bearer = HTTPBearer()


class JWTPayload(TypedDict):
    sub: str
    role: str
    exp: int
    iat: int
    

def create_jwt_token(user_id: int, role: RoleInSystem) -> str:
    """
    Генерирует JWT токен.
    """
    try:
        expiration_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=5)
        
        payload = {
            "sub": str(user_id),  
            "role": role.name,  # Используем name для сериализации в строку
            "exp": int(expiration_time.timestamp()),
            "iat": int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
        }

        encoded_jwt = jwt.encode(
            payload,
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        raise Exception(f"Error creating JWT token: {e}")

async def decode_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(jwt_bearer)) -> dict:
    """
    Декодирует JWT токен, извлечённый из заголовка Authorization.
    """
    try:
        token = credentials.credentials  # Извлекаем строку токена из credentials
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def role_required(required_roles: List[RoleInSystem] = None):
    """
    Зависимость для проверки ролей пользователя из JWT токена.
    Возвращает payload токена, если проверка прошла успешно.
    """
    def role_checker(token: dict = Depends(decode_jwt_token)) -> dict:
        user_role = token.get("role")
        if required_roles is None:
            return token
        
        try:
            user_role_enum = RoleInSystem[user_role]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Invalid role in token"
            )
            
        if user_role_enum not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Insufficient permissions"
            )
        return token
    return role_checker