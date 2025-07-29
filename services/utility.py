""" carry functions that makes code bulky"""
from fastapi import Request, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from config import get_settings
from datetime import timedelta, datetime
from database import model, script
from passlib.context import CryptContext
from sqlalchemy import or_
from sqlalchemy.orm import Session

bcrpyt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


def generate_jwt(username, expires_delta):
    encode = {'sub': username}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    jwt_token = jwt.encode(encode, get_settings().SECRET_KEY, algorithm=get_settings().ALGORITHM)
    return jwt_token

#checks availability of user's username and password
def authenticate_user(username:str, password: str, expires_delta: timedelta, db:script.db_session):
        
    find_user = db.query(model.User).all()

    for eachrow in find_user:
        if eachrow.email == username and bcrpyt_context.verify(password, eachrow.password):
            return generate_jwt(username, expires_delta)
    else:
        return False  # Authentication failed
    
    
def get_user_from_token(request: Request, db: Session):
    """
    Decode the JWT token, extract username/email, 
    then authenticate if the user exists in the database.
    Returns the user if authenticated, else raises 401 Unauthorized.
    """
    try:
        token = request.cookies.get("access_token")
        if not token:
            return None 
        # Decode the token
        payload = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
        username: str = payload.get("sub")
        
        if not username:
            return None
        
        # Query the user
        user = db.query(model.User).filter(model.User.email == username).first()
        if user:
            return user
        return None
    
    except JWTError:  # Catches token-related errors
        return None
    
def validate_password(password, password2, msg_list):
    if password != password2:
        msg_list.append("Passwords do not match")
        return False
    if len(password) < 8:
        msg_list.append("Password should be at least 8 characters long")
        return False
    return True

def get_line_manager(db, user):
    try:
        cmd_level = int(user.cmd_level)
    except Exception:
        return None
    # Search for a line manager in the same department, starting from one level lower and continuing down
    for level in range(cmd_level - 1, 0, -1):
        lm = db.query(model.User).filter(
            model.User.organization_id == user.organization_id,
            model.User.department == user.department,
            model.User.cmd_level == str(level).zfill(3)
        ).first()
        if lm:
            return lm
    # Fallback: search for any user with the required command level in the organization
    for level in range(cmd_level - 1, 0, -1):
        lm = db.query(model.User).filter(
            model.User.organization_id == user.organization_id,
            model.User.cmd_level == str(level).zfill(3)
        ).first()
        if lm:
            return lm
    return None
