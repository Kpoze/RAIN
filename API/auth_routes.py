from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import schemas, model, api_auth
from .database import get_db

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=schemas.UserPublic)
def create_user(user_credentials: schemas.UserCreate, db: Session = Depends(get_db)):
    
    # ... (la vérification de l'email existant ne change pas)

    hashed_password = api_auth.get_password_hash(user_credentials.password)
    
    # MODIFICATION: On ajoute first_name et last_name lors de la création
    new_user = model.User(
        email=user_credentials.email, 
        hashed_password=hashed_password,
        first_name=user_credentials.first_name,
        last_name=user_credentials.last_name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    user = db.query(model.User).filter(model.User.email == user_credentials.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    if not api_auth.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    access_token = api_auth.create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}