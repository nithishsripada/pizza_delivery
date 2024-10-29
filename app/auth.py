from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.database import SessionLocal
from app.models import User
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import verify_password, create_access_token
from sqlalchemy.orm import Session
from app.main import app
SECRET_KEY = "your_secret_key"  # Replace with a strong key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
       return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
       return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
       to_encode = data.copy()
       expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
       to_encode.update({"exp": expire})
       encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
       return encoded_jwt

def get_user_by_email(db: Session, email: str):
       return db.query(User).filter(User.email == email).first()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(SessionLocal)):
       try:
           payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
           email: str = payload.get("sub")
           if email is None:
               raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
           user = get_user_by_email(db, email)
           if user is None:
               raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
       except JWTError:
           raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
       return user

#

async def get_current_active_user(current_user: User = Depends(get_current_user)):
       if current_user is None:
           raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
       return current_user

async def get_current_admin(current_user: User = Depends(get_current_active_user)):
       if current_user.role != "admin":
           raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
       return current_user

async def get_current_delivery_partner(current_user: User = Depends(get_current_active_user)):
       if current_user.role != "delivery_partner":
           raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
       return current_user

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(SessionLocal)):
       user = db.query(User).filter(User.email == form_data.username).first()
       if not user or not verify_password(form_data.password, user.password):
           raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
       access_token = create_access_token(data={"sub": user.email})
       return {"access_token": access_token, "token_type": "bearer"}