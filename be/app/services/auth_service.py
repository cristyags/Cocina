from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.repositories import user_repo
from app.schemas.token import TokenData
from app.schemas.user import UserCreate


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> TokenData:
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    subject = payload.get("sub")
    return TokenData(user_id=int(subject) if subject is not None else None)


def register(db: Session, data: UserCreate):
    password_hash = hash_password(data.password)
    return user_repo.create(
        db,
        username=data.username,
        email=data.email,
        password_hash=password_hash,
        full_name=data.full_name,
        role="waiter",
    )


def login(db: Session, username: str, password: str) -> str | None:
    user = user_repo.get_by_username(db, username)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return create_access_token(user.id)
