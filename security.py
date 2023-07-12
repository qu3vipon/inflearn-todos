from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


def get_access_token(
    auth_header: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> str:
    if auth_header is None:
        raise HTTPException(status_code=401, detail="Not Authorized")
    return auth_header.credentials  # access_token
