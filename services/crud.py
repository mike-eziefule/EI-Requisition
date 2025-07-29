from sqlalchemy.orm import Session
from database.model import Requisition, LineItem, Expense, ExpenseLineItem
from datetime import datetime
from database import model
from services.utility import bcrpyt_context


def create_requisition(
    db: Session, 
    request_number: str, 
    description: str,
    status: str,
    requestor_id: int,
    line_items_data: list
    ):
    
    if status == "NULL":
        status = "Approved"
        
    try:
        # Check for duplicate request_number before creating
        existing = db.query(Requisition).filter(Requisition.request_number == request_number).first()
        if existing:
            raise Exception("Request number already exists. Please use a unique request number.")

        # Create the Requisition record
        requisition = Requisition(
            request_number = request_number, 
            description = description,
            status = status,
            timestamp = datetime.now(),
            requestor_id = requestor_id,
        )
    
        db.add(requisition)
        db.commit()
        db.refresh(requisition)  # Get the Requisition with the newly generated ID

        # Create line items
        for line_item in line_items_data:
            # Accept both dicts and Pydantic objects
            if hasattr(line_item, "dict"):
                line_item_data = line_item.dict()
            else:
                line_item_data = dict(line_item)  # Ensure it's a dict

            item = LineItem(
                item_name=line_item_data.get("item_name"),
                quantity=line_item_data.get("quantity"),
                category=line_item_data.get("category"),
                item_reason=line_item_data.get("item_reason"),
                requisition_id=requisition.id
            )
            db.add(item)

        db.commit()  #Save line items to the database
        db.refresh(requisition)  #Get the updated requisition with line items
        return True

    except Exception as e:
        db.rollback()  #Rollback in case of error
        raise Exception(f"Error in create_requisition: {str(e)}")


def get_all_requisitions(db: Session):
    return db.query(Requisition).all()

def get_requisition_by_id(db: Session, requisition_id: int):
    return db.query(Requisition).filter(Requisition.id == requisition_id).first()

def update_requisition_status(db: Session, requisition_id: int, status: str):
    requisition = get_requisition_by_id(db, requisition_id)
    if requisition:
        requisition.status = status
        db.commit()
        return requisition
    return None


def to_dict(self):
    return {
        "id": self.id,
        "request_number": self.request_number,
        "description": self.description,
        "status": self.status
    }


def create_expense(
    db: Session,
    expense_number: str,
    description: str,
    status: str,
    requestor_id: int,
    attachment_path: str,
    line_items_data: list,
    total: float
):
    if status == "NULL":
        status = "Approved"
        
    try:
        # Check for duplicate expense_number before creating
        existing = db.query(Expense).filter(Expense.expense_number == expense_number).first()
        if existing:
            raise Exception("Expense number already exists. Please use a unique expense number.")

        expense = Expense(
            expense_number=expense_number,
            description=description,
            status=status,
            timestamp=datetime.now(),
            requestor_id=requestor_id,
            attachment_path=attachment_path,
            total=total,
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)

        for line_item in line_items_data:
            # Accept both dicts and Pydantic objects
            if hasattr(line_item, "dict"):
                line_item_data = line_item.dict()
            else:
                line_item_data = dict(line_item)  # Ensure it's a dict

            item = ExpenseLineItem(
                item_name=line_item_data.get("item_name"),
                quantity=line_item_data.get("quantity"),
                category=line_item_data.get("category"),
                price=line_item_data.get("price"),
                amount=line_item_data.get("amount"),
                expense_id=expense.id
            )
            db.add(item)

        db.commit()
        db.refresh(expense)
        return True

    except Exception as e:
        db.rollback()
        raise Exception(f"Error in create_expense: {str(e)}")


def create_organization(db, organization_name, rc_number, address, product):
    new_org = model.Organization(
        organization_name=organization_name,
        rc_number=rc_number,
        address=address,
        product=product,
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return new_org

def create_owner_user(db, organization_name, staff_name, designation, email, password, role, organization_id):
    new_owner = model.User(
        organization_name=organization_name,
        staff_name=staff_name,
        designation=designation,
        email=email,
        password=bcrpyt_context.hash(password),
        role=role,
        date=datetime.now().date(),
        organization_id=organization_id,
        cmd_level="001",
        department="management"
    )
    db.add(new_owner)
    db.commit()
    db.refresh(new_owner)
    return new_owner
