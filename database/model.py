from httpx import request
from database.script import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, UUID
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
    
    staff = relationship("User", back_populates="organization")


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index = True)
    organization_name = Column(String, nullable=False)
    staff_name = Column(String, nullable=False)
    designation = Column(String, nullable=False)
    line_manager = Column(String, nullable=True)
    email = Column(String, nullable= False, unique=True)
    password = Column(String, nullable= False)
    date = Column(Date, nullable= False)
    organization_id = Column(String(36), ForeignKey("organization.id"))

    # Relationships
    organization = relationship("Organization", back_populates="staff")
    requests = relationship("Requisition", back_populates="requestor")


class Requisition(Base):
    __tablename__ = "requisitions"
    
    id = Column(Integer, primary_key=True, index=True)
    request_number = Column(String, unique=True)
    description = Column(String)
    attachment_path = Column(String, nullable=True)
    status = Column(String, default="Pending")
    timestamp = Column(DateTime, nullable=False)  # DateTime column to store date and time
    requestor_id = Column(Integer, ForeignKey("users.id"))

    # Relationship to line items
    line_items = relationship("LineItem", back_populates="requisition")
    requestor = relationship("User", back_populates="requests")

class LineItem(Base):
    __tablename__ = "line_items"
    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String)
    quantity = Column(Integer)
    category = Column(String)
    item_reason = Column(String)
    requisition_id = Column(Integer, ForeignKey("requisitions.id"))

    requisition = relationship("Requisition", back_populates="line_items")
