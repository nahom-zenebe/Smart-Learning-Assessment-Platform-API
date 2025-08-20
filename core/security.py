from passlib.context import CryptContext
from datatime import datetime,timedelta
from jose import jwt
from app.config import JWT_SECRET, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context=CryptoContext(schemes=['bcrypt'])


def hash_password(password:str):
    return pwd_context.hash(password)

def verify_password(password:str,hashed_password:str):
    return pwd_context.verify(password,hashed_password)

def create_access_token(data:dict,expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode=data.copy()
    expire=datetime.utcnow()+timedelta(minutes=expires_delta)
    to_encode.update({"exp":expire})
    encoded_jwt=jwt.encode(to_encode,JWT_SECRET,algorithm="HS256")

    return encoded_jwt
