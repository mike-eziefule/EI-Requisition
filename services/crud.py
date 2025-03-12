from sqlalchemy.orm import Session
from database.model import Requisition, LineItem
from datetime import datetime


def create_requisition(
    db: Session, 
    request_number: str, 
    description: str,
    status: str,
    requestor_id: int,
    attachment_path: str, 
    line_items_data: list
    ):
    
    try:
        # Create the Requisition record
        requisition = Requisition(
            request_number = request_number, 
            description = description,
            status = status,
            timestamp = datetime.now(),
            requestor_id = requestor_id,
            attachment_path = attachment_path,
        )
    
        db.add(requisition)
        db.commit()
        db.refresh(requisition)  # Get the Requisition with the newly generated ID

        # Create line items
        for line_item in line_items_data:
            item = LineItem(
                item_name=line_item["item_name"],
                quantity=line_item["quantity"],
                category=line_item["category"],
                item_reason=line_item["item_reason"],
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