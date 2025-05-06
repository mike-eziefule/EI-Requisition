from pydantic import BaseModel
from typing import List, Optional


# Pydantic model to handle the input form data
class LineItemInput(BaseModel):
    id: Optional[int]  # Optional ID for existing line items
    item_name: str
    quantity: int
    category: str
    item_reason: str

class RequisitionInput(BaseModel):
    request_number: str
    description: str
    line_items: List[LineItemInput]  # List of line items

# Pydantic model for updating requisition status
class StatusUpdate(BaseModel):
    requisition_id: int
    status: str  # "approved" or "denied"