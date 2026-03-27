from fastapi import Header, HTTPException

from .security import decode_access_token


async def get_current_claims(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(status_code=401, detail='Missing bearer token')
    token = authorization.split(' ', 1)[1]
    try:
        return decode_access_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail='Invalid token') from exc
