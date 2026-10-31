
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.sessions import verify_session

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    """Authenticate a request using its Bearer session token."""

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    user = verify_session(credentials.credentials)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session"
        )

    return user


