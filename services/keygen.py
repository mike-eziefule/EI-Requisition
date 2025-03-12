"""Helper functions to generate Keys."""
import secrets
import string
from sqlalchemy.orm import Session
from database import model


#function 1
def get_url_by_key(key:str, db:Session) -> model.Requisition:
    """Return a URL by specified key."""
    return (
        db.query(model.Requisition)
        .filter(model.Requisition.request_number == key)
        .first()
    )

#function 2
def create_random_key(length: int = 5) -> str:
    """Return a random key of the specified length."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


#function 3
def create_unique_random_key(db:Session) -> str:
    """Create a guaranteed random key."""
    key = create_random_key()
    while get_url_by_key(key, db):
        key = create_random_key()
    return key

