# SPDX-License-Identifier: GPL-3.0-or-later
#
# Toolify: Empower any LLM with function calling capabilities.
# Copyright (C) 2025 FunnyCups (https://github.com/funnycups)

import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Security scheme
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data model"""
    username: str
    exp: datetime


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def generate_jwt_secret() -> str:
    """Generate a secure random JWT secret"""
    return secrets.token_urlsafe(48)


def create_access_token(username: str, secret_key: str, expires_delta: timedelta = timedelta(hours=24)) -> str:
    """Create a JWT access token"""
    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "sub": username,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str, secret_key: str) -> Optional[str]:
    """Verify a JWT token and return the username if valid"""
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_admin_credentials():
    """Dependency to get admin credentials from config"""
    from config_loader import config_loader
    config = config_loader.config
    
    if not config.admin_authentication:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication is not configured"
        )
    
    return config.admin_authentication


async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    admin_config = Depends(get_admin_credentials)
) -> str:
    """Dependency to verify admin token"""
    token = credentials.credentials
    username = verify_token(token, admin_config.jwt_secret)
    
    if username != admin_config.username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    return username

