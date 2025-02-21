from database.script import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Float, UUID
from sqlalchemy.orm import relationship
import uuid

class Organization(Base):
    __tablename__ = 'organization'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index = True)
    organization_name = Column(String, nullable= False)
    address = Column(String, nullable= True)
    rc_number = Column(String, nullable= True)
    admin_name = Column(String, nullable= False, default="IT manager")
    email = Column(String, nullable= False, unique=True)
    password = Column(String, nullable= False)
    product = Column(String, nullable= False)
    

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index = True)
    organization_name = Column(String, nullable=False)
    staff_name = Column(String, nullable=False)
    designation = Column(String, nullable=False)
    email = Column(String, nullable= False, unique=True)
    password = Column(String, nullable= False)
    date = Column(Date, nullable= False)
    organization_id = Column(String, nullable=False)
