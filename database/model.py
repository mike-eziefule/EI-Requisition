from httpx import request
from database.script import Base
from sqlalchemy import Column, Float, Integer, String, ForeignKey, DateTime, Date, UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

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
    profile_picture_url = Column(String, nullable=True)
    
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
    profile_picture_url = Column(String, nullable= True)
    organization_id = Column(String(36), ForeignKey("organization.id"))

    # Relationships
    organization = relationship("Organization", back_populates="staff")
    requests = relationship("Requisition", back_populates="requestor")


class Requisition(Base):
    __tablename__ = "requisitions"
    
    id = Column(Integer, primary_key=True, index=True)
    request_number = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, nullable=False, default="Pending")
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)  # DateTime column to store date and time
    requestor_id = Column(Integer, ForeignKey("users.id"))

    # Relationship to line items
    line_items = relationship("LineItem", back_populates="requisition")
    requestor = relationship("User", back_populates="requests")
    comments = relationship("RequisitionComment", back_populates="requisition")


class LineItem(Base):
    __tablename__ = "line_items"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Auto-incrementing primary key
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    item_reason = Column(String, nullable=False)
    requisition_id = Column(Integer, ForeignKey("requisitions.id"))

    requisition = relationship("Requisition", back_populates="line_items")


class RequisitionComment(Base):
    __tablename__ = "requisition_comments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requisition_id = Column(Integer, ForeignKey("requisitions.id"), nullable=False)
    comment = Column(String, nullable=False)
    created_by = Column(String, nullable=False)  # Line manager's name or email
    created_at = Column(DateTime, default=datetime.utcnow)

    requisition = relationship("Requisition", back_populates="comments")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    expense_number = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    attachment_path = Column(String, nullable=True)
    status = Column(String, nullable=False, default="Pending")
    total= Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    requestor_id = Column(Integer, ForeignKey("users.id"))

    # Relationship to line items
    line_items = relationship("ExpenseLineItem", back_populates="expense")
    requestor = relationship("User")
    expense_comments = relationship("ExpenseComment", back_populates="expense")


class ExpenseLineItem(Base):
    __tablename__ = "expense_line_items"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)
    expense_id = Column(Integer, ForeignKey("expenses.id"))

    expense = relationship("Expense", back_populates="line_items")


class ExpenseComment(Base):
    __tablename__ = "expense_comments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    comment = Column(String, nullable=False)
    created_by = Column(String, nullable=False)  # Line manager's name or email
    created_at = Column(DateTime, default=datetime.utcnow)

    expense = relationship("Expense", back_populates="expense_comments")

