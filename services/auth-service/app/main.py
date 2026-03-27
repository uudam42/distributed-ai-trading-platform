from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from shared.app.audit import record_audit
from shared.app.config import settings
from shared.app.db import get_db
from shared.app.logging_utils import configure_logging, log_kv
from shared.app.models import Account, User
from shared.app.schemas import HealthResponse, LoginRequest, TokenResponse
from shared.app.security import create_access_token, verify_password
app = FastAPI(title='Auth Service')
logger = configure_logging('auth-service')


@app.get('/health', response_model=HealthResponse)
def health():
    return HealthResponse(status='ok', service=settings.service_name)


@app.post('/auth/login', response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        log_kv(logger, 'AuthService', 'login_failed', email=request.email)
        raise HTTPException(status_code=401, detail='Invalid credentials')
    account = db.query(Account).filter(Account.user_id == user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail='Account not found')
    token = create_access_token(str(user.id), {'email': user.email, 'account_id': str(account.id)})
    record_audit(db, 'auth.login.succeeded.v1', {'user_id': str(user.id), 'account_id': str(account.id), 'email': user.email}, str(user.id))
    log_kv(logger, 'AuthService', 'login_succeeded', user=user.email, account_id=account.id)
    return TokenResponse(access_token=token, user_id=user.id, account_id=account.id)


# TODO(Phase2): Add stronger auth flows, refresh tokens, and API key rotation.
