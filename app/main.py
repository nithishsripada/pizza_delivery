#Update main.py to create database tables if they don’t exist.
# app/main.py
from fastapi import FastAPI
from app.database import get_db
from app.models import Base
from app.routes import admin, customer, delivery
from app.schemas import UserCreate
from app.auth import get_password_hash
from app.database import SessionLocal
from app.models import User
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

app = FastAPI()
# Create database tables
# initlialize the database tables

Base.metadata.create_all(bind=engine)
@app.get("/")
def read_root():
    return {"message": "Pizza Delivery System"}

# Include the routers

app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(customer.router, prefix="/customer", tags=["Customer"])
app.include_router(delivery.router, prefix="/delivery", tags=["Delivery"])


@app.post("/register/")
async def register(user: UserCreate, db: Session = Depends(SessionLocal)):
       db_user = db.query(User).filter(User.email == user.email).first()
       if db_user:
           raise HTTPException(status_code=400, detail="Email already registered")
       hashed_password = get_password_hash(user.password)
       new_user = User(email=user.email, password=hashed_password, role=user.role, name=user.name)
       db.add(new_user)
       db.commit()
       db.refresh(new_user)
       return {"msg": "User registered successfully", "user_id": new_user.id}