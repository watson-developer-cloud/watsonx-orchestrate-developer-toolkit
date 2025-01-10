from fastapi import Depends
from typing import Optional, Dict, Any
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

# This example allows any bearer or api keys to be valid
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


async def get_api_key(api_key_header: str = Depends(api_key_header)) -> Optional[str]:
    return api_key_header


async def get_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> Optional[str]:
    return credentials.credentials if credentials else None


async def get_current_user(
    api_key: Optional[str] = Depends(get_api_key),
    token: Optional[str] = Depends(get_bearer_token),
) -> Dict[str, Any]:
    return {"api_key": api_key, "token": token}
